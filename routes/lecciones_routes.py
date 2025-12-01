from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime
import random

from database.db import get_db
from models.user import Usuario
from models.leccion import Leccion
from models.video import Video
from models.usuario_leccion import UsuarioLeccion
from middleware.auth_middleware import require_auth

router = APIRouter()


# ============== SCHEMAS ==============

class LessonDetailResponse(BaseModel):
    id_leccion: int
    titulo: str
    id_modulo: int
    orden: int
    completado: bool
    videos: list[dict]

class QuestionResponse(BaseModel):
    id_leccion: int
    pregunta: str
    respuesta_correcta: str
    respuestas_incorrectas: list[str]
    imagen_url: str | None
    video_url: str | None

class AnswerRequest(BaseModel):
    respuesta: str

class AnswerResponse(BaseModel):
    correcto: bool
    mensaje: str
    leccion_completada: bool


# ============== ENDPOINTS ==============

@router.get("/{leccion_id}", response_model=LessonDetailResponse)
async def get_lesson_detail(
    leccion_id: int,
    current_user: dict = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """
    Get lesson details with videos
    """
    user_id = current_user["userId"]
    
    # Get lesson
    leccion = db.query(Leccion).filter(Leccion.id_leccion == leccion_id).first()
    if not leccion:
        raise HTTPException(status_code=404, detail="Leccion no encontrada")
    
    # Get videos for this lesson
    videos = db.query(Video).filter(
        Video.id_leccion == leccion_id,
        Video.activo == True
    ).order_by(Video.orden).all()
    
    # Get user progress
    usuario_leccion = db.query(UsuarioLeccion).filter(
        UsuarioLeccion.id_usuario == user_id,
        UsuarioLeccion.id_leccion == leccion_id
    ).first()
    
    return LessonDetailResponse(
        id_leccion=leccion.id_leccion,
        titulo=leccion.titulo,
        id_modulo=leccion.id_modulo,
        orden=leccion.orden,
        completado=bool(usuario_leccion.completado) if usuario_leccion else False,
        videos=[{
            "id_video": v.id_video,
            "titulo": v.titulo,
            "url": v.url,
            "duracion_seg": v.duracion_seg,
            "orden": v.orden
        } for v in videos]
    )


@router.get("/{leccion_id}/question", response_model=QuestionResponse)
async def get_lesson_question(
    leccion_id: int,
    current_user: dict = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """
    Get a quiz question for this lesson
    Returns a random video as the question with wrong answers from other videos
    """
    user_id = current_user["userId"]
    
    # Get lesson
    leccion = db.query(Leccion).filter(Leccion.id_leccion == leccion_id).first()
    if not leccion:
        raise HTTPException(status_code=404, detail="Leccion no encontrada")
    
    # Get videos for this lesson (these are the "words")
    videos = db.query(Video).filter(
        Video.id_leccion == leccion_id,
        Video.activo == True
    ).all()
    
    if not videos:
        raise HTTPException(status_code=404, detail="No hay videos en esta leccion")
    
    # Pick a random video as the question
    video_correcto = random.choice(videos)
    
    # Get other videos from same lesson for wrong answers
    otros_videos = [v for v in videos if v.id_video != video_correcto.id_video]
    
    # If not enough wrong answers in this lesson, get from other lessons
    if len(otros_videos) < 3:
        otros_videos_extra = db.query(Video).filter(
            Video.id_leccion != leccion_id,
            Video.activo == True
        ).limit(3 - len(otros_videos)).all()
        otros_videos.extend(otros_videos_extra)
    
    # Select up to 3 wrong answers
    respuestas_incorrectas = [v.titulo for v in random.sample(otros_videos, min(3, len(otros_videos)))]
    
    return QuestionResponse(
        id_leccion=leccion_id,
        pregunta=f"¿Qué palabra representa este video?",
        respuesta_correcta=video_correcto.titulo,
        respuestas_incorrectas=respuestas_incorrectas,
        imagen_url=None,
        video_url=video_correcto.url
    )


@router.post("/{leccion_id}/answer", response_model=AnswerResponse)
async def submit_answer(
    leccion_id: int,
    request: AnswerRequest,
    current_user: dict = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """
    Submit an answer for the lesson quiz
    Marks lesson as completed if correct
    """
    user_id = current_user["userId"]
    
    # Get lesson
    leccion = db.query(Leccion).filter(Leccion.id_leccion == leccion_id).first()
    if not leccion:
        raise HTTPException(status_code=404, detail="Leccion no encontrada")
    
    # Check if video with this title exists in lesson
    video = db.query(Video).filter(
        Video.id_leccion == leccion_id,
        Video.titulo == request.respuesta,
        Video.activo == True
    ).first()
    
    # Get or create user lesson progress
    usuario_leccion = db.query(UsuarioLeccion).filter(
        UsuarioLeccion.id_usuario == user_id,
        UsuarioLeccion.id_leccion == leccion_id
    ).first()
    
    if not usuario_leccion:
        usuario_leccion = UsuarioLeccion(
            id_usuario=user_id,
            id_leccion=leccion_id,
            completado=False,
            intentos=0,
            calificacion=0
        )
        db.add(usuario_leccion)
    
    # Increment attempts
    usuario_leccion.intentos = (usuario_leccion.intentos or 0) + 1
    usuario_leccion.actualizado_en = datetime.utcnow()
    
    if video:
        # Correct answer
        usuario_leccion.completado = True
        usuario_leccion.calificacion = 100
        db.commit()
        
        return AnswerResponse(
            correcto=True,
            mensaje="¡Correcto! Has completado esta leccion.",
            leccion_completada=True
        )
    else:
        # Wrong answer
        db.commit()
        
        return AnswerResponse(
            correcto=False,
            mensaje="Respuesta incorrecta. Intenta de nuevo.",
            leccion_completada=False
        )
