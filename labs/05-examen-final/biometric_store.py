"""Datos biométricos locales: 3-5 embeddings por usuario, sin fotografías."""
import re, numpy as np
from pathlib import Path
class BiometricStoreError(Exception):pass
class BiometricStore:
    def __init__(self,storage_dir=None):
        self.storage_dir=Path(storage_dir or Path(__file__).parent/'rostros');self.storage_dir.mkdir(parents=True,exist_ok=True)
    def _get_path(self,user_id):
        if not isinstance(user_id,str) or not re.fullmatch(r'[a-zA-Z0-9_-]{1,64}',user_id):raise BiometricStoreError('ID inválido')
        return self.storage_dir/(user_id+'.npz')
    def save_embeddings(self,user_id,embeddings):
        array=np.asarray(embeddings,dtype=np.float32).reshape(-1,128)
        if not 3<=len(array)<=5 or not np.isfinite(array).all():raise BiometricStoreError('Se requieren 3 a 5 embeddings válidos')
        np.savez_compressed(self._get_path(user_id),embeddings=array)
    def load_embedding(self,user_id):
        path=self._get_path(user_id)
        if not path.exists():raise BiometricStoreError('Usuario sin enrolamiento')
        with np.load(path,allow_pickle=False) as data:
            return data['embeddings'].astype(np.float32)
    def delete_embedding(self,user_id):
        path=self._get_path(user_id)
        if path.exists():path.unlink();return True
        return False
