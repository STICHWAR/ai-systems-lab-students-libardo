"""Adaptador Telegram por long polling. Toda la lógica vive en Core y AuthenticationService."""
import asyncio,logging,os,tempfile
from contextlib import AsyncExitStack
from pathlib import Path
from dotenv import load_dotenv
from telegram import Update,InlineKeyboardButton,InlineKeyboardMarkup
from telegram.ext import Application,CommandHandler,MessageHandler,CallbackQueryHandler,ContextTypes,filters
from sessions import Sessions
from audit import Audit
from authentication_service import AuthenticationService
from confirmations import ConfirmationRegistry, ConfirmationError
from core import Core
from orchestrator import create_orchestrator

log=logging.getLogger('examen_final')
class Channel:
    def __init__(self,sessions,audit,core,auth):
        self.sessions=sessions;self.audit=audit;self.core=core;self.auth=auth
        self.history={};self.history_identity={};self.confirmations=ConfirmationRegistry()
    async def start(self,update,ctx):
        await update.message.reply_text('Soy el Asistente del Curso de IA desarrollado por Santiago Villamizar y Libardo Bravo. Puedes hacer preguntas públicas o usar /login. /ayuda para comandos.')
    async def who(self,update,ctx):
        uid=update.effective_user.id;had_session=uid in self.sessions.active;s=self.sessions.get(uid)
        if had_session and not s:self.audit.write(uid,'sesion_expirada')
        await update.message.reply_text(f'Telegram ID: {uid}\nSesión: '+(f"autenticada como {s['nombre']} ({s['rol']})" if s else 'pública / expirada'))
    async def login(self,update,ctx):
        uid=update.effective_user.id
        try:
            ch=self.auth.begin_login(uid)
            options={'izquierda':'Gira lentamente la cabeza a tu IZQUIERDA','derecha':'Gira lentamente la cabeza a tu DERECHA','acercar':'Acerca tu rostro a la cámara'}
            await update.message.reply_text('Reto de prueba de vida (60 segundos): '+options[ch['option']]+'. Envía una VIDEO-NOTA circular grabada ahora. Una foto o video normal no sirve.')
        except PermissionError:await update.message.reply_text('Cuenta no autorizada o temporalmente bloqueada.')
    async def logout(self,update,ctx):
        uid=update.effective_user.id;self.sessions.logout(uid);self.audit.write(uid,'logout')
        self.history.pop(update.effective_chat.id,None);self.history_identity.pop(update.effective_chat.id,None)
        await update.message.reply_text('Sesión cerrada.')
    async def help(self,update,ctx):
        await update.message.reply_text('/start: presentación\n/quiensoy: ID y sesión\n/login: reto facial\n/logout: cerrar sesión\n/ayuda: comandos')
    async def video(self,update,ctx):
        uid=update.effective_user.id
        if not update.message.video_note:
            await update.message.reply_text('Solo se admite una video-nota circular para autenticación.');return
        if not self.sessions.pending.get(uid):
            try:
                await asyncio.to_thread(self.auth.reject_missing_challenge,uid)
            except PermissionError:
                pass
            await update.message.reply_text('Escribe /login antes de enviar tu video-nota.');return
        # video-notes reenviadas son rechazadas antes de descargar
        forwarded=bool(update.message.forward_origin)
        path=None
        try:
            if forwarded:
                await asyncio.to_thread(self.auth.reject_pending,uid,'VideoNotaReenviada')
            tf=await ctx.bot.get_file(update.message.video_note.file_id)
            with tempfile.NamedTemporaryFile(suffix='.mp4',delete=False) as f:path=Path(f.name)
            await tf.download_to_drive(custom_path=path)
            user=await asyncio.to_thread(self.auth.login,uid,path,True,forwarded)
            await update.message.reply_text(f"Hola, {user['nombre']} ({user['rol']}). Sesión iniciada correctamente.")
        except Exception:
            log.exception('Fallo de autenticación para ID %s',uid)
            await update.message.reply_text('No se pudo autenticar. Solicita un reto nuevo con /login.')
        finally:
            if path:path.unlink(missing_ok=True)
    async def bad_media(self,update,ctx):
        uid=update.effective_user.id
        # Sólo cuenta como intento si existe un reto iniciado explícitamente.
        # Así no se penalizan fotos enviadas fuera de una prueba de /login.
        if self.sessions.pending.get(uid):
            try:
                await asyncio.to_thread(self.auth.reject_pending,uid,'FormatoMediaInvalido')
            except PermissionError:
                pass
        await update.message.reply_text('Para /login solo se permite una video-nota circular, no fotos ni videos adjuntos.')
    async def text(self,update,ctx):
        uid=update.effective_user.id; chat=update.effective_chat.id
        # En grupos, responder solo en privado: impedir fuga de datos académicos.
        if update.effective_chat.type!='private':
            await update.message.reply_text('Por privacidad, utiliza el bot en un chat privado.');return
        had_session=uid in self.sessions.active;s=self.sessions.get(uid)
        if had_session and not s:self.audit.write(uid,'sesion_expirada')
        identity=(s.get('id') if s else None)
        if self.history_identity.get(chat)!=identity:
            self.history.pop(chat,None)
            self.history_identity[chat]=identity
        hist=self.history.setdefault(chat,[])
        async def confirm(tool,args):
            loop=asyncio.get_running_loop();future=loop.create_future()
            request=self.confirmations.create(uid,chat,tool.name,args,future)
            buttons=InlineKeyboardMarkup([[InlineKeyboardButton('Sí',callback_data=f'confirm:{request.token}:yes'),InlineKeyboardButton('No',callback_data=f'confirm:{request.token}:no')]])
            await update.message.reply_text(f"¿Confirmas ejecutar {tool.name} con {args}?",reply_markup=buttons)
            try:return await asyncio.wait_for(future,timeout=45)
            except asyncio.TimeoutError:return False
            finally:self.confirmations.cancel(uid,request.token)
        try:
            result=await self.core.responder(update.message.text,hist,s,confirm,uid)
            await update.message.reply_text(result.text[:3900])
            hist.extend([{'role':'user','content':update.message.text},{'role':'assistant','content':result.text}]);del hist[:-20]
        except Exception:
            log.exception('Error de LLM/MCP para ID %s',uid)
            await update.message.reply_text('El servicio está temporalmente indisponible. Inténtalo de nuevo.')
    async def callback(self,update,ctx):
        query=update.callback_query;uid=update.effective_user.id
        try:
            _,token,decision=query.data.split(':',2)
            accepted=self.confirmations.resolve(uid,update.effective_chat.id,token,decision=='yes')
        except (ValueError, ConfirmationError):
            accepted=False
        if not accepted:
            await query.answer('Confirmación inválida o vencida.',show_alert=True)
            return
        await query.answer()
        await query.edit_message_text('Confirmación recibida.' if decision=='yes' else 'Acción cancelada.')

async def run():
    load_dotenv();logging.basicConfig(level=logging.INFO)
    # httpx registra URLs completas en INFO; para Telegram contienen el token
    # en la ruta. El adaptador conserva sus propios eventos sin exponer secretos.
    logging.getLogger('httpx').setLevel(logging.WARNING)
    logging.getLogger('httpcore').setLevel(logging.WARNING)
    token=os.getenv('TELEGRAM_BOT_TOKEN')
    if not token:raise RuntimeError('Falta TELEGRAM_BOT_TOKEN en .env')
    sessions=Sessions();audit=Audit()
    async with AsyncExitStack() as stack:
        # La confirmación real se proporciona por solicitud en Core.
        async def deny(tool,args):return False
        orchestrator=await create_orchestrator(stack,deny)
        auth=AuthenticationService(sessions=sessions,audit=audit)
        channel=Channel(sessions,audit,Core(orchestrator,audit),auth)
        app=Application.builder().token(token).concurrent_updates(True).build()
        for name,handler in [('start',channel.start),('quiensoy',channel.who),('login',channel.login),('logout',channel.logout),('ayuda',channel.help)]:app.add_handler(CommandHandler(name,handler))
        app.add_handler(CallbackQueryHandler(channel.callback,pattern=r'^confirm:[A-Za-z0-9_-]{20,40}:(yes|no)$'))
        app.add_handler(MessageHandler(filters.VIDEO_NOTE,channel.video))
        app.add_handler(MessageHandler(filters.PHOTO|filters.VIDEO,channel.bad_media))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND,channel.text))
        # PTB run_polling no se puede llamar dentro de un loop ya abierto.
        async with app:
            await app.start();await app.updater.start_polling()
            log.info('Bot iniciado por long polling')
            try:await asyncio.Event().wait()
            finally:await app.updater.stop();await app.stop()
if __name__=='__main__':
    try:asyncio.run(run())
    except KeyboardInterrupt:pass
