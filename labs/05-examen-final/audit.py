"""Log de seguridad: ninguna imagen, video, embedding ni credencial."""
import json, time
from pathlib import Path
class Audit:
    def __init__(self,path=None):self.path=Path(path or Path(__file__).parent/'auditoria.jsonl')
    def write(self,telegram_id,event,reason=None,similarity=None,tool=None):
        row={'timestamp':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'telegram_user_id':str(telegram_id),'evento':event,'motivo':reason,'similitud':similarity,'tool':tool}
        self.path.parent.mkdir(parents=True,exist_ok=True)
        with self.path.open('a',encoding='utf-8') as out:out.write(json.dumps(row,ensure_ascii=False)+'\n')
