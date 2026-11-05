"""Sesiones por identificador de Telegram y retos de un solo uso."""
from __future__ import annotations
from dataclasses import dataclass
import json, os, secrets, time
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()

@dataclass
class Session:
    telegram_id: int
    user: dict
    expires: float

class Sessions:
    def __init__(self,users_file=None, clock=time.time):
        self.clock=clock; self.users_file=Path(users_file or Path(__file__).parent/'data/usuarios.json')
        self.users=json.loads(self.users_file.read_text(encoding='utf-8'))['usuarios']
        self.active={}; self.pending={}; self.failures={};self.used_challenges=set()
        self.ttl=int(os.getenv('SESSION_MINUTES','10'))*60
        self.timeout=int(os.getenv('LIVENESS_TIMEOUT_SECONDS','60'))
        self.max_attempts=int(os.getenv('LOGIN_MAX_ATTEMPTS','3'))
        self.block_seconds=int(os.getenv('LOGIN_BLOCK_MINUTES','5'))*60
    def user(self,tg_id):
        return next((u for u in self.users if u.get('telegram_user_id') is not None and str(u['telegram_user_id'])==str(tg_id)),None)
    def get(self,tg_id):
        obj=self.active.get(int(tg_id))
        if obj and self.clock() < obj.expires: return obj.user.copy()
        self.active.pop(int(tg_id),None)
        return None
    def logout(self,tg_id):
        self.active.pop(int(tg_id),None);self.pending.pop(int(tg_id),None)
    def blocked(self,tg_id):
        n, until = self.failures.get(int(tg_id),(0,0))
        if self.clock()<until: return True
        if until: self.failures.pop(int(tg_id),None)
        return False
    def begin(self,tg_id):
        tg_id=int(tg_id)
        if self.blocked(tg_id): raise PermissionError('Temporalmente bloqueado')
        if not self.user(tg_id): raise PermissionError('Cuenta de Telegram no registrada')
        options=['izquierda','derecha','acercar']
        challenge={'id':secrets.token_urlsafe(24),'option':secrets.choice(options),'issued':self.clock(),'telegram_id':tg_id}
        self.pending[tg_id]=challenge
        return challenge.copy()
    def consume(self,tg_id,challenge_id=None):
        tg_id=int(tg_id); challenge=self.pending.pop(tg_id,None)
        if not challenge or (challenge_id is not None and challenge['id']!=challenge_id): raise PermissionError('Reto inexistente')
        if challenge['id'] in self.used_challenges: raise PermissionError('Reto reutilizado')
        self.used_challenges.add(challenge['id'])
        if self.clock()-challenge['issued']>self.timeout: raise PermissionError('Reto vencido')
        if self.blocked(tg_id): raise PermissionError('Temporalmente bloqueado')
        return challenge
    def failed(self,tg_id):
        tg_id=int(tg_id); n,until=self.failures.get(tg_id,(0,0)); n+=1
        if n>=self.max_attempts: self.failures[tg_id]=(0,self.clock()+self.block_seconds)
        else: self.failures[tg_id]=(n,0)
    def success(self,tg_id):
        u=self.user(tg_id)
        if not u: raise PermissionError('Cuenta no registrada')
        self.active[int(tg_id)]=Session(int(tg_id),u.copy(),self.clock()+self.ttl)
        self.failures.pop(int(tg_id),None)
        return u.copy()
