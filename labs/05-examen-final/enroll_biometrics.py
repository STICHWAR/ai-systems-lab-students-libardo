"""Enrolamiento LOCAL bajo consentimiento: nunca vía Telegram."""
import argparse
from pathlib import Path
from sessions import Sessions
from face_auth import FaceAuthenticator, FaceAuthenticationError
from biometric_store import BiometricStore
from image_normalization import load_enrollment_bgr

def enroll(user_id,telegram_id,paths,consent=False):
    if not consent:raise PermissionError('Consentimiento explícito requerido')
    if len(paths)<3 or len(paths)>5:raise ValueError('Se necesitan 3 a 5 fotografías')
    users=Sessions(); user=next((u for u in users.users if u['id']==user_id),None)
    if not user or str(user.get('telegram_user_id'))!=str(telegram_id):raise PermissionError('ID y Telegram no coinciden con usuarios.json')
    auth=FaceAuthenticator();vectors=[]
    for path in paths:
        photo_path=Path(path)
        photo=load_enrollment_bgr(photo_path)
        try:
            vectors.append(auth.extract_embedding(photo))
        except Exception as exc:
            raise FaceAuthenticationError(f'{photo_path.name}: {exc}') from exc
        del photo
    BiometricStore().save_embeddings(user_id,vectors)
    return len(vectors)
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--user',required=True);parser.add_argument('--telegram-id',required=True);parser.add_argument('--fotos',nargs='+',required=True);parser.add_argument('--consiento',action='store_true')
    a=parser.parse_args();print('Embeddings guardados:',enroll(a.user,a.telegram_id,a.fotos,a.consiento))
