from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

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
