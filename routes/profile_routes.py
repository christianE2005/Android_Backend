from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime

from database.db import get_db
from models.user import Usuario
from middleware.auth_middleware import require_auth

router = APIRouter()


# ============== SCHEMAS ==============

class ProfileResponse(BaseModel):
    id_usuario: int
    nombre: str
    correo: str
    monedas: int
    es_admin: bool
    creado_en: str | None

class UpdateProfileRequest(BaseModel):
    nombre: str | None = None


# ============== ENDPOINTS ==============

@router.get("/me", response_model=ProfileResponse)
async def get_profile(
    current_user: dict = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """
    Get current user's profile
    """
    user_id = current_user["userId"]
    
    user = db.query(Usuario).filter(Usuario.id_usuario == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    return ProfileResponse(
        id_usuario=user.id_usuario,
        nombre=user.nombre,
        correo=user.correo,
        monedas=user.monedas or 0,
        es_admin=bool(user.es_admin),
        creado_en=user.creado_en.isoformat() if user.creado_en else None
    )


@router.put("/update", response_model=ProfileResponse)
async def update_profile(
    request: UpdateProfileRequest,
    current_user: dict = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """
    Update current user's profile (nombre)
    """
    user_id = current_user["userId"]
    
    user = db.query(Usuario).filter(Usuario.id_usuario == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    # Update fields if provided
    if request.nombre is not None:
        user.nombre = request.nombre
    
    user.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(user)
    
    return ProfileResponse(
        id_usuario=user.id_usuario,
        nombre=user.nombre,
        correo=user.correo,
        monedas=user.monedas or 0,
        es_admin=bool(user.es_admin),
        creado_en=user.creado_en.isoformat() if user.creado_en else None
    )
