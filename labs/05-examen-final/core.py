"""Núcleo desacoplado del canal, con autorización ANTES y DURANTE cada tool."""
import json
from access import precheck,allowed_tools
from agent import Agent
from capabilities import rag_tool
from orchestrator import OrchestratorAnswer,create_orchestrator
from tools import Tool

class Core:
    def __init__(self,orchestrator,audit=None):self.o=orchestrator;self.audit=audit
    async def responder(self,pregunta,historial=None,sesion=None,confirm=None,telegram_id=None):
        role=sesion.get('rol','publico') if sesion else 'publico'
        if role not in ('publico','estudiante','docente'): role='publico'
        refusal=precheck(pregunta,role,sesion.get('codigo_estudiante') if sesion else None)
        if refusal:
            if self.audit:self.audit.write(telegram_id,'acceso_denegado',refusal)
            return OrchestratorAnswer(text=refusal,mode='agente')
        return await self.answer(pregunta,historial or [],sesion,confirm,telegram_id)
    async def answer(self,question,history,session,confirm,telegram_id):
        role=session.get('rol','publico') if session else 'publico'
        names=allowed_tools(role)
        tools=[]
        for original in self.o.action_tools:
            if original.name not in names:continue
            # El estudiante recibe únicamente el wrapper que inyecta su código
            # de sesión; nunca la tool MCP original con parámetro ``codigo``.
            if role == 'estudiante' and original.name == 'solicitar_supletorio':continue
            # Captura role en el cierre para aplicar un segundo check al ejecutar.
            async def run(args,tool=original):
                from access import authorize_tool
                if not authorize_tool(role,tool.name):raise PermissionError('Tool bloqueada')
                result=await tool.run(args)
                if self.audit and tool.name not in ('fecha_actual','dias_hasta','calcular_nota_final'):
                    self.audit.write(telegram_id,'tool_restringida_ejecutada' if tool.name not in allowed_tools('publico') else 'tool_ejecutada',tool=tool.name)
                return result
            tools.append(Tool(original.name,original.description,original.parameters,run,original.read_only,original.origin))
        # Tools de estudiante nunca reciben código del modelo: se inyecta desde sesión.
        if role == 'estudiante' and session:
            code=session.get('codigo_estudiante')
            if code:
                mapping={'consultar_mis_notas':'consultar_notas','consultar_mis_solicitudes':'consultar_solicitudes'}
                for alias,actual in mapping.items():
                    raw=next((t for t in self.o.action_tools if t.name==actual),None)
                    if raw:
                        async def run_mine(args,tool=raw,tool_name=alias):
                            if not session or not session.get('codigo_estudiante'):raise PermissionError('Sin identidad')
                            result=await tool.run({'codigo':session['codigo_estudiante']})
                            # El servidor MCP también atiende al docente. Antes de devolver
                            # datos al LLM de un estudiante se elimina el único campo que
                            # corresponde exclusivamente al personal docente.
                            if tool_name == 'consultar_mis_notas':
                                payload=json.loads(result)
                                if isinstance(payload,dict):
                                    payload.pop('observaciones_docente',None)
                                    return json.dumps(payload,ensure_ascii=False)
                            return result
                        tools.append(Tool(alias,'Consulta exclusivamente datos de la cuenta autenticada',{'type':'object','properties':{},'additionalProperties':False},run_mine,True,'mcp'))
                original=next((t for t in self.o.action_tools if t.name=='solicitar_supletorio'),None)
                if original:
                    params={'type':'object','properties':{k:v for k,v in original.parameters.get('properties',{}).items() if k!='codigo'},'required':[k for k in original.parameters.get('required',[]) if k!='codigo']}
                    async def run_supletorio(args,tool=original,authenticated_code=code):
                        if not authenticated_code:raise PermissionError('Sin identidad')
                        return await tool.run({**args,'codigo':authenticated_code})
                    tools.append(Tool('solicitar_supletorio','Solicita supletorio solo para el usuario autenticado',params,run_supletorio,False,'mcp'))
        tools.append(rag_tool(self.o.rag,authenticated_role=role))
        async def ask(tool,args):
            if confirm is None:return False
            return await confirm(tool,args)
        agent=Agent(self.o.llm,tools,ask,self.o.max_steps)
        result=await agent.run(question,history)
        return self.o._from_agent(result,'agente')
