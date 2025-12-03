from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional

from database.db import get_db
from models.user import Usuario
from models.usuario_modulo import UsuarioModulo
from models.modulo import Modulo
from models.leccion import Leccion
from models.usuario_leccion import UsuarioLeccion
from models.video import Video
from middleware.auth_middleware import require_auth

router = APIRouter()


# ============== SCHEMAS ==============

class ModuleInfo(BaseModel):
    name: str
    current: int
    max: int
    id: int


class ModulosResponse(BaseModel):
    modulos: list[ModuleInfo]


class LessonInfo(BaseModel):
    name: str
    current: int
    max: int
    id: int


class LeccionesResponse(BaseModel):
    modulo_id: int
    modulo_nombre: str
    lecciones: list[LessonInfo]


# ---- Nuevos schemas para CRUD de módulos ----

class ModuloBase(BaseModel):
    titulo: str
    orden: int
    activo: bool = True


class ModuloCreate(ModuloBase):
    """Datos necesarios para crear un módulo."""
    pass


class ModuloUpdate(BaseModel):
    """Datos opcionales para actualizar un módulo."""
    titulo: Optional[str] = None
    orden: Optional[int] = None
    activo: Optional[bool] = None


class ModuloDB(ModuloBase):
    """Cómo regresaremos el módulo en las respuestas."""
    id_modulo: int

    class Config:
        orm_mode = True


# ============== ENDPOINTS ==============

@router.get("/", response_model=ModulosResponse)
async def get_modulos(
    current_user: dict = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """
    Get all modules with user's progress
    Returns: list of modules with name, current progress, max value, and id
    """
    user_id = current_user["userId"]

    # Verify user exists
    user = db.query(Usuario).filter(Usuario.id_usuario == user_id).first()
    if not user:
        raise HTTPException(
            status_code=404,
            detail="Usuario no encontrado"
        )

    # Get all active modules
    modulos = db.query(Modulo).filter(
        Modulo.activo == True
    ).order_by(Modulo.orden).all()

    # Get user's progress for each module
    modulos_response = []
    for modulo in modulos:
        # Get user progress for this module
        usuario_modulo = db.query(UsuarioModulo).filter(
            UsuarioModulo.id_usuario == user_id,
            UsuarioModulo.id_modulo == modulo.id_modulo
        ).first()

        # Calculate current progress (progreso_pct is 0-100, we convert to 0-50 scale)
        current = int(float(usuario_modulo.progreso_pct or 0) / 100) if usuario_modulo else 0

        modulos_response.append(ModuleInfo(
            name=modulo.titulo,
            current=current,
            max=50,
            id=modulo.id_modulo
        ))

    return ModulosResponse(modulos=modulos_response)


@router.get("/{modulo_id}/lecciones", response_model=LeccionesResponse)
async def get_lecciones_by_modulo(
    modulo_id: int,
    current_user: dict = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """
    Get all lessons for a specific module with user's progress
    Returns: list of lessons with name, current videos watched, max videos, and id
    """
    user_id = current_user["userId"]

    # Verify user exists
    user = db.query(Usuario).filter(Usuario.id_usuario == user_id).first()
    if not user:
        raise HTTPException(
            status_code=404,
            detail="Usuario no encontrado"
        )

    # Verify module exists
    modulo = db.query(Modulo).filter(Modulo.id_modulo == modulo_id).first()
    if not modulo:
        raise HTTPException(
            status_code=404,
            detail="Módulo no encontrado"
        )

    # Get all active lessons for this module
    lecciones = db.query(Leccion).filter(
        Leccion.id_modulo == modulo_id,
        Leccion.activo == True
    ).order_by(Leccion.orden).all()

    # Build response with progress for each lesson
    lecciones_response = []
    for leccion in lecciones:
        # Count total videos in this lesson (max)
        total_videos = db.query(Video).filter(
            Video.id_leccion == leccion.id_leccion,
            Video.activo == True
        ).count()

        # Get user's progress for this lesson
        usuario_leccion = db.query(UsuarioLeccion).filter(
            UsuarioLeccion.id_usuario == user_id,
            UsuarioLeccion.id_leccion == leccion.id_leccion
        ).first()

        # Calculate current progress based on calificacion or intentos
        # If completed, current = max; otherwise calculate from calificacion percentage
        if usuario_leccion:
            if usuario_leccion.completado:
                current = total_videos
            else:
                # Use calificacion as percentage of completion
                current = int(float(usuario_leccion.calificacion or 0) / 100 * total_videos)
        else:
            current = 0

        lecciones_response.append(LessonInfo(
            name=leccion.titulo,
            current=current,
            max=total_videos,
            id=leccion.id_leccion
        ))

    return LeccionesResponse(
        modulo_id=modulo_id,
        modulo_nombre=modulo.titulo,
        lecciones=lecciones_response
    )


# ---------- NUEVOS ENDPOINTS CRUD PARA MÓDULOS ----------

@router.post("/", response_model=ModuloDB)
async def create_modulo(
    data: ModuloCreate,
    current_user: dict = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """
    Crear un nuevo módulo.
    """
    nuevo_modulo = Modulo(
        titulo=data.titulo,
        orden=data.orden,
        activo=data.activo
    )

    db.add(nuevo_modulo)
    db.commit()
    db.refresh(nuevo_modulo)

    return nuevo_modulo


@router.put("/{modulo_id}", response_model=ModuloDB)
async def update_modulo(
    modulo_id: int,
    data: ModuloUpdate,
    current_user: dict = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """
    Editar un módulo existente.
    Solo se actualizan los campos que se envíen.
    """
    modulo = db.query(Modulo).filter(Modulo.id_modulo == modulo_id).first()
    if not modulo:
        raise HTTPException(status_code=404, detail="Módulo no encontrado")

    if data.titulo is not None:
        modulo.titulo = data.titulo
    if data.orden is not None:
        modulo.orden = data.orden
    if data.activo is not None:
        modulo.activo = data.activo

    db.commit()
    db.refresh(modulo)

    return modulo


@router.delete("/{modulo_id}")
async def delete_modulo(
    modulo_id: int,
    current_user: dict = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """
    Eliminar módulo (borrado físico).
    Elimina la fila completa de la tabla 'modulos'.
    """
    modulo = db.query(Modulo).filter(Modulo.id_modulo == modulo_id).first()
    if not modulo:
        raise HTTPException(status_code=404, detail="Módulo no encontrado")

    db.delete(modulo)
    db.commit()

    return {"mensaje": "Módulo eliminado correctamente"}

