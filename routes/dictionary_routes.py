from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional

from database.db import get_db
from models.video import Video
from models.leccion import Leccion
from models.modulo import Modulo
from middleware.auth_middleware import require_auth

router = APIRouter()


# ============== SCHEMAS ==============

class WordInfo(BaseModel):
    id: int
    titulo: str
    url: str
    duracion_seg: int | None
    leccion: str
    modulo: str


class DictionaryResponse(BaseModel):
    total: int
    palabras: list[WordInfo]


class WordDetailResponse(BaseModel):
    id: int
    titulo: str
    url: str
    duracion_seg: int | None
    leccion_id: int
    leccion_nombre: str
    modulo_id: int
    modulo_nombre: str


# ---- Nuevos schemas para CRUD de videos ----

class VideoBase(BaseModel):
    id_leccion: int
    titulo: str
    url: str
    duracion_seg: int | None = None
    orden: int
    activo: bool = True


class VideoCreate(VideoBase):
    """Datos necesarios para crear un video."""
    pass


class VideoUpdate(BaseModel):
    """Datos opcionales para actualizar un video."""
    id_leccion: Optional[int] = None
    titulo: Optional[str] = None
    url: Optional[str] = None
    duracion_seg: Optional[int] = None
    orden: Optional[int] = None
    activo: Optional[bool] = None


# ============== ENDPOINTS ==============

@router.get("/", response_model=DictionaryResponse)
async def get_dictionary(
    search: str | None = None,
    current_user: dict = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """
    Get all words (videos) in the dictionary
    Optionally filter by search term
    """
    # Base query joining videos with lessons and modules
    query = db.query(Video, Leccion, Modulo).join(
        Leccion, Video.id_leccion == Leccion.id_leccion
    ).join(
        Modulo, Leccion.id_modulo == Modulo.id_modulo
    ).filter(Video.activo == True)

    # Apply search filter if provided
    if search:
        query = query.filter(Video.titulo.ilike(f"%{search}%"))

    # Order by module, lesson, then video order
    results = query.order_by(Modulo.orden, Leccion.orden, Video.orden).all()

    palabras = []
    for video, leccion, modulo in results:
        palabras.append(WordInfo(
            id=video.id_video,
            titulo=video.titulo,
            url=video.url,
            duracion_seg=video.duracion_seg,
            leccion=leccion.titulo,
            modulo=modulo.titulo
        ))

    return DictionaryResponse(
        total=len(palabras),
        palabras=palabras
    )


@router.get("/{word_id}", response_model=WordDetailResponse)
async def get_word_detail(
    word_id: int,
    current_user: dict = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """
    Get detailed information about a specific word (video)
    """
    result = db.query(Video, Leccion, Modulo).join(
        Leccion, Video.id_leccion == Leccion.id_leccion
    ).join(
        Modulo, Leccion.id_modulo == Modulo.id_modulo
    ).filter(Video.id_video == word_id).first()

    if not result:
        raise HTTPException(status_code=404, detail="Palabra no encontrada")

    video, leccion, modulo = result

    return WordDetailResponse(
        id=video.id_video,
        titulo=video.titulo,
        url=video.url,
        duracion_seg=video.duracion_seg,
        leccion_id=leccion.id_leccion,
        leccion_nombre=leccion.titulo,
        modulo_id=modulo.id_modulo,
        modulo_nombre=modulo.titulo
    )


# ---------- NUEVOS ENDPOINTS CRUD PARA VIDEOS ----------

@router.post("/", response_model=WordDetailResponse)
async def create_video(
    data: VideoCreate,
    current_user: dict = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """
    Crear un nuevo video (palabra del diccionario).
    """
    # Validar que la lección exista
    leccion = db.query(Leccion).filter(Leccion.id_leccion == data.id_leccion).first()
    if not leccion:
        raise HTTPException(status_code=404, detail="Lección no encontrada")

    nuevo_video = Video(
        id_leccion=data.id_leccion,
        titulo=data.titulo,
        url=data.url,
        duracion_seg=data.duracion_seg,
        orden=data.orden,
        activo=data.activo,
    )

    db.add(nuevo_video)
    db.commit()
    db.refresh(nuevo_video)

    # Volvemos a hacer el join para regresar el mismo formato de detalle
    result = db.query(Video, Leccion, Modulo).join(
        Leccion, Video.id_leccion == Leccion.id_leccion
    ).join(
        Modulo, Leccion.id_modulo == Modulo.id_modulo
    ).filter(Video.id_video == nuevo_video.id_video).first()

    video, leccion, modulo = result

    return WordDetailResponse(
        id=video.id_video,
        titulo=video.titulo,
        url=video.url,
        duracion_seg=video.duracion_seg,
        leccion_id=leccion.id_leccion,
        leccion_nombre=leccion.titulo,
        modulo_id=modulo.id_modulo,
        modulo_nombre=modulo.titulo
    )


@router.put("/{word_id}", response_model=WordDetailResponse)
async def update_video(
    word_id: int,
    data: VideoUpdate,
    current_user: dict = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """
    Editar un video existente.
    Solo se actualizan los campos que se envíen.
    """
    video = db.query(Video).filter(Video.id_video == word_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="Video no encontrado")

    # Si se cambia de lección, validar la nueva lección
    if data.id_leccion is not None:
        leccion = db.query(Leccion).filter(Leccion.id_leccion == data.id_leccion).first()
        if not leccion:
            raise HTTPException(status_code=404, detail="Lección destino no encontrada")
        video.id_leccion = data.id_leccion

    if data.titulo is not None:
        video.titulo = data.titulo
    if data.url is not None:
        video.url = data.url
    if data.duracion_seg is not None:
        video.duracion_seg = data.duracion_seg
    if data.orden is not None:
        video.orden = data.orden
    if data.activo is not None:
        video.activo = data.activo

    db.commit()
    db.refresh(video)

    # Join para regresar detalle completo
    result = db.query(Video, Leccion, Modulo).join(
        Leccion, Video.id_leccion == Leccion.id_leccion
    ).join(
        Modulo, Leccion.id_modulo == Modulo.id_modulo
    ).filter(Video.id_video == video.id_video).first()

    video, leccion, modulo = result

    return WordDetailResponse(
        id=video.id_video,
        titulo=video.titulo,
        url=video.url,
        duracion_seg=video.duracion_seg,
        leccion_id=leccion.id_leccion,
        leccion_nombre=leccion.titulo,
        modulo_id=modulo.id_modulo,
        modulo_nombre=modulo.titulo
    )


@router.delete("/{word_id}")
async def delete_video(
    word_id: int,
    current_user: dict = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """
    Eliminar video (borrado físico).
    Elimina la fila completa de la tabla 'videos'.
    """
    video = db.query(Video).filter(Video.id_video == word_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="Video no encontrado")

    db.delete(video)
    db.commit()

    return {"mensaje": "Video eliminado correctamente"}

