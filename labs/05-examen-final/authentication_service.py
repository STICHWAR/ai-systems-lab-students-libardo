"""Verificación uno a uno: video-nota + reto consumible + vínculo Telegram."""
import os
from sessions import Sessions
from biometric_store import BiometricStore
from face_auth import FaceAuthenticator
from liveness import LivenessDetector
from audit import Audit
class AuthenticationService:
    def __init__(self,sessions=None,biometrics=None,facial=None,liveness=None,audit=None):
        self.sessions=sessions or Sessions()
        self.biometrics=biometrics or BiometricStore()
        self.facial=facial or FaceAuthenticator(threshold=float(os.getenv('FACE_MATCH_THRESHOLD','.363')))
        self.liveness=liveness or LivenessDetector(self.facial)
        self.audit=audit or Audit()
    def login(self,tg_id,path,is_video_note=True,is_forwarded=False):
        sim=None
        try:
            # Consumir siempre el desafío, incluso si el video fracasa.
            challenge=self.sessions.consume(tg_id)
            if not is_video_note or is_forwarded:raise PermissionError('Formato o procedencia inválidos')
            user=self.sessions.user(tg_id)
            if not user:raise PermissionError('Cuenta sin registro')
            live=self.liveness.analyze_video(path,challenge['option'])
            refs=self.biometrics.load_embedding(user['id'])
            candidate=self.facial.extract_embedding(live['frontal_frame'])
            match=self.facial.compare_embeddings(refs,candidate)
            sim=match['similarity']
            if not match['matched']:raise PermissionError('No coincide la identidad')
            identity=self.sessions.success(tg_id)
            self.audit.write(tg_id,'login_aceptado',similarity=sim)
            return identity
        except Exception as exc:
            self.sessions.failed(tg_id)
            # Los PermissionError proceden de controles deterministas (reto
            # vencido, formato, identidad); su texto es un motivo técnico y
            # no incluye el medio ni datos biométricos.
            reason=str(exc) if isinstance(exc,PermissionError) else type(exc).__name__
            self.audit.write(tg_id,'login_rechazado',reason=reason,similarity=sim)
            raise PermissionError('No se pudo completar el inicio de sesión.') from exc
    def reject_pending(self,tg_id,reason):
        """Rechaza un medio antes de descargarlo, consumiendo el reto pendiente.

        Se usa para formatos no admitidos y reenvíos. El reto se consume y el
        fallo cuenta igual que una autenticación inválida, sin procesar video.
        """
        try:
            self.sessions.consume(tg_id)
        except Exception as exc:
            self.audit.write(tg_id,'login_rechazado',reason=type(exc).__name__)
            raise PermissionError('No hay un reto válido pendiente.') from exc
        self.sessions.failed(tg_id)
        self.audit.write(tg_id,'login_rechazado',reason=reason)
        raise PermissionError('Medio rechazado.')
    def begin_login(self,tg_id):
        """Inicia un reto y deja auditoría determinista cuando no puede hacerlo."""
        try:
            return self.sessions.begin(tg_id)
        except PermissionError as exc:
            event='login_bloqueado' if self.sessions.blocked(tg_id) else 'login_inicio_rechazado'
            self.audit.write(tg_id,event,reason=str(exc))
            raise
    def reject_missing_challenge(self,tg_id):
        """Registra un intento con reto inexistente o previamente consumido.

        No incrementa el contador de fallos porque no había un reto válido que
        pudiera autenticarse.
        """
        self.audit.write(tg_id,'login_rechazado',reason='RetoInexistenteOReutilizado')
        raise PermissionError('No hay un reto válido pendiente.')
