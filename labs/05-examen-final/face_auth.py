"""YuNet + SFace. Verificación facial uno a uno con varias muestras."""
import os
import cv2, numpy as np
from pathlib import Path
class FaceAuthenticationError(Exception):pass
class FaceAuthenticator:
    def __init__(self,models_dir=None,threshold=0.363, detection_threshold=None):
        d=Path(models_dir or Path(__file__).parent/'models')
        det=d/'face_detection_yunet_2023mar.onnx'; rec=d/'face_recognition_sface_2021dec.onnx'
        if not det.exists() or not rec.exists():raise FileNotFoundError('Descarga los modelos YuNet y SFace en models/ (no subir a Git)')
        # Este umbral solo decide si YuNet detecta un rostro. La identidad se
        # sigue validando después con el umbral SFace FACE_MATCH_THRESHOLD.
        self.score_threshold=float(detection_threshold if detection_threshold is not None else os.getenv('FACE_DETECTION_THRESHOLD','0.90'))
        if not 0.0 < self.score_threshold <= 1.0:raise ValueError('FACE_DETECTION_THRESHOLD debe estar entre 0 y 1')
        self.nms_threshold=0.3
        self.top_k=5000
        self.detector=cv2.FaceDetectorYN_create(str(det),'',(320,320),self.score_threshold,self.nms_threshold,self.top_k)
        self.recognizer=cv2.FaceRecognizerSF_create(str(rec),'')
        self.threshold=float(threshold)
    def extract_embedding(self,image):
        if image is None or not isinstance(image,np.ndarray):raise FaceAuthenticationError('Imagen inválida')
        h,w=image.shape[:2];self.detector.setInputSize((w,h));_,faces=self.detector.detect(image)
        if faces is None:raise FaceAuthenticationError('No se detectó ningún rostro')
        if len(faces)!=1:raise FaceAuthenticationError(f'Deben aparecer exactamente un rostro; se detectaron {len(faces)}')
        return self.recognizer.feature(self.recognizer.alignCrop(image,faces[0])).ravel().astype(np.float32)
    def similarities(self,references,candidate):
        refs=np.asarray(references,dtype=np.float32).reshape(-1,128);candidate=np.asarray(candidate,dtype=np.float32).reshape(1,128)
        return [float(self.recognizer.match(r.reshape(1,128),candidate,cv2.FaceRecognizerSF_FR_COSINE)) for r in refs]
    def compare_embeddings(self,reference,candidate):
        similarity=max(self.similarities(reference,candidate))
        return {'similarity':similarity,'matched':similarity>=self.threshold}
