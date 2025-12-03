from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime
import random
from typing import Optional  # 👈 nuevo

from database.db import get_db
from models.user import Usuario
from models.leccion import Leccion
from models.video import Video
from models.usuario_leccion import UsuarioLeccion
from models.modulo import Modulo  # 👈 para validar id_modulo
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
    calificacion: float  # Calificación de 0 a 100


class AnswerResponse(BaseModel):
    mensaje: str
    leccion_completada: bool
    calificacion: float


# ---- Nuevos schemas para CRUD de lecciones ----

class LeccionBase(BaseModel):
    id_modulo: int
    titulo: str
    orden: int
    activo: bool = True


class LeccionCreate(LeccionBase):
    """Datos necesarios para crear una lección."""
    pass


class LeccionUpdate(BaseModel):
    """Datos opcionales para actualizar una lección."""
    id_modulo: Optional[int] = None
    titulo: Optional[str] = None
    orden: Optional[int] = None
    activo: Optional[bool] = None


class LeccionDB(LeccionBase):
    """Cómo regresaremos la lección en las respuestas."""
    id_leccion: int

    class Config:
        orm_mode = True


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
    Submit the grade for a lesson quiz
    Marks lesson as completed based on the grade
    """
    user_id = current_user["userId"]

    # Get lesson
    leccion = db.query(Leccion).filter(Leccion.id_leccion == leccion_id).first()
    if not leccion:
        raise HTTPException(status_code=404, detail="Leccion no encontrada")

    # Validate calificacion range
    if request.calificacion < 0 or request.calificacion > 100:
        raise HTTPException(status_code=400, detail="La calificación debe estar entre 0 y 100")

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
    usuario_leccion.calificacion = request.calificacion
    usuario_leccion.actualizado_en = datetime.utcnow()

    # Mark as completed if grade >= 70 (puedes cambiar este umbral)
    leccion_completada = request.calificacion >= 100
    usuario_leccion.completado = leccion_completada

    db.commit()

    if leccion_completada:
        mensaje = f"¡Felicidades! Has completado esta lección con {request.calificacion}%"
    else:
        mensaje = f"Obtuviste {request.calificacion}%. Necesitas al menos 70% para completar la lección."

    return AnswerResponse(
        mensaje=mensaje,
        leccion_completada=leccion_completada,
        calificacion=request.calificacion
    )


# ---------- NUEVOS ENDPOINTS CRUD PARA LECCIONES ----------

@router.post("/", response_model=LeccionDB)
async def create_leccion(
    data: LeccionCreate,
    current_user: dict = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """
    Crear una nueva lección.
    """
    # Validar que el módulo exista
    modulo = db.query(Modulo).filter(Modulo.id_modulo == data.id_modulo).first()
    if not modulo:
        raise HTTPException(status_code=404, detail="Módulo no encontrado")

    nueva_leccion = Leccion(
        id_modulo=data.id_modulo,
        titulo=data.titulo,
        orden=data.orden,
        activo=data.activo
    )

    db.add(nueva_leccion)
    db.commit()
    db.refresh(nueva_leccion)

    return nueva_leccion


@router.put("/{leccion_id}", response_model=LeccionDB)
async def update_leccion(
    leccion_id: int,
    data: LeccionUpdate,
    current_user: dict = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """
    Editar una lección existente.
    Solo se actualizan los campos que se envíen.
    """
    leccion = db.query(Leccion).filter(Leccion.id_leccion == leccion_id).first()
    if not leccion:
        raise HTTPException(status_code=404, detail="Leccion no encontrada")

    # Si quieren moverla de módulo, validar el módulo nuevo
    if data.id_modulo is not None:
        modulo = db.query(Modulo).filter(Modulo.id_modulo == data.id_modulo).first()
        if not modulo:
            raise HTTPException(status_code=404, detail="Módulo destino no encontrado")
        leccion.id_modulo = data.id_modulo

    if data.titulo is not None:
        leccion.titulo = data.titulo
    if data.orden is not None:
        leccion.orden = data.orden
    if data.activo is not None:
        leccion.activo = data.activo

    db.commit()
    db.refresh(leccion)

    return leccion


@router.delete("/{leccion_id}")
async def delete_leccion(
    leccion_id: int,
    current_user: dict = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """
    Eliminar lección (borrado físico).
    Elimina la fila completa de la tabla 'lecciones'.
    """
    leccion = db.query(Leccion).filter(Leccion.id_leccion == leccion_id).first()
    if not leccion:
        raise HTTPException(status_code=404, detail="Leccion no encontrada")

    db.delete(leccion)
    db.commit()

    return {"mensaje": "Leccion eliminada correctamente"}
