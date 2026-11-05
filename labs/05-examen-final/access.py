"""Política central de autorización: fallar cerrado, nunca confiar en el LLM."""
from dataclasses import dataclass
import re

LEVELS = {'publico': {'publico'}, 'estudiante': {'publico','estudiante'}, 'docente': {'publico','estudiante','docente'}}
PUBLIC_TOOLS = {'buscar_documentos','consultar_calendario','fecha_actual','dias_hasta','calcular_nota_final','calcular_nota_necesaria'}
STUDENT_TOOLS = {'consultar_mis_notas','consultar_mis_solicitudes','solicitar_supletorio'}
TEACHER_TOOLS = {'consultar_notas','consultar_solicitudes','registrar_nota'}
RESTRICTED_HINTS = ('simulacro','monitoría','monitoria','rúbrica interna','rubrica interna','casos especiales','caso especial','ajuste de horario','oficina 210')
ACADEMIC_HINTS = ('nota','calificación','calificacion','supletorio','solicitud','observaciones_docente','observaciones del docente')

def allowed_tools(role):
    if role not in LEVELS: raise PermissionError('Rol inválido')
    names = set(PUBLIC_TOOLS)
    if role in ('estudiante','docente'): names |= STUDENT_TOOLS
    if role == 'docente': names |= TEACHER_TOOLS
    return names

def authorize_tool(role, name):
    return name in allowed_tools(role)

def precheck(question,role,own_code=None):
    """Denegaciones explícitas ANTES del modelo; las preguntas permitidas se filtran vía RAG."""
    if role not in LEVELS: raise PermissionError('Rol inválido')
    q=question.casefold()
    if role == 'publico' and any(w in q for w in RESTRICTED_HINTS + ACADEMIC_HINTS):
        return 'Esta información requiere iniciar sesión con /login.'
    if role == 'estudiante':
        if any(w in q for w in ('observaciones','casos especiales','caso especial','ajuste de horario','rúbrica interna','rubrica interna','oficina 210')):
            return 'Tu rol no tiene acceso a esa información.'
        # Los códigos institucionales no deben asumir un prefijo concreto ni
        # eliminar ceros iniciales. Se detectan secuencias de 6 a 12 dígitos.
        codes=re.findall(r'\b\d{6,12}\b|<codigo_[12]>',q)
        if any(code!=str(own_code).lower() for code in codes):
            return 'No puedes consultar información de otro estudiante.'
        if any(w in q for w in ('registra un','registrar_nota','consultar_notas','consultar_solicitudes')):
            return 'Tu rol no tiene permiso para ejecutar esa operación.'
    return None
