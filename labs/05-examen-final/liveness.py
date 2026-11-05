"""Liveness por reto aleatorio: desplazamiento orientado o acercamiento; limitación: no anti-deepfake."""
import cv2,numpy as np
from pathlib import Path
from face_auth import FaceAuthenticator,FaceAuthenticationError
class LivenessError(Exception):pass
class LivenessDetector:
    def __init__(self,auth=None): self.auth=auth or FaceAuthenticator()
    def analyze_video(self,path,challenge):
        if challenge not in ('izquierda','derecha','acercar'):raise LivenessError('Reto inválido')
        cap=cv2.VideoCapture(str(path))
        if not cap.isOpened():raise LivenessError('Video inválido')
        trajectory=[]; frontal=None;frames=0; valid=0; embeddings=[]
        try:
            while frames<420:
                ok,frame=cap.read()
                if not ok:break
                frames+=1
                if frames%3!=0:continue
                h,w=frame.shape[:2];self.auth.detector.setInputSize((w,h))
                _,faces=self.auth.detector.detect(frame)
                if faces is None or len(faces)!=1:raise LivenessError('Debe aparecer exactamente un rostro durante toda la grabación')
                f=faces[0];valid+=1
                # desplazamiento de nariz normalizado por separación ocular (YuNet landmarks)
                left,right=f[4:6],f[6:8];nose=f[8:10]
                eye_dist=max(np.linalg.norm(left-right),1e-6)
                offset=float((nose[0]-(left[0]+right[0])/2)/eye_dist)
                size=float(f[2]*f[3]/(w*h))
                trajectory.append((offset,size))
                # frame más frontal (nariz centrada respecto a ojos)
                if frontal is None or abs(offset)<frontal[0]:frontal=(abs(offset),frame.copy())
                if valid%5==0:
                    embeddings.append(self.auth.extract_embedding(frame))
        finally:cap.release()
        if valid<7 or not trajectory:raise LivenessError('Frames faciales insuficientes')
        arr=np.asarray(trajectory)
        # exigimos una transición en dirección del reto, no solo movimiento arbitrario
        left_shift=float(np.min(arr[:,0])-arr[0,0]);right_shift=float(np.max(arr[:,0])-arr[0,0])
        near=float(np.max(arr[:,1])/max(arr[0,1],1e-8))
        movement={'izquierda':left_shift<-.16,'derecha':right_shift>.16,'acercar':near>1.35}[challenge]
        if not movement:raise LivenessError('Movimiento del reto no detectado')
        # Identidad consistente: similitud par a par entre frames
        if len(embeddings)>1:
            for emb in embeddings[1:]:
                if not self.auth.compare_embeddings(embeddings[0],emb)['matched']:raise LivenessError('Identidad inconsistente durante el video')
        return {'live':True,'frontal_frame':frontal[1],'frames':valid,'reto':challenge,'desplazamiento_izquierda':left_shift,'desplazamiento_derecha':right_shift,'escala':near}
    def close(self):pass
