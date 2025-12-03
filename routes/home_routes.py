from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta

from database.db import get_db
from models.user import Usuario
from models.desafio_diario import DesafioDiario
from models.usuario_modulo import UsuarioModulo
from models.modulo import Modulo
from middleware.auth_middleware import require_auth

router = APIRouter()


class HomeResponse(BaseModel):
    Usuario: dict
    Dias: dict
    Misiones: int
    Progreso: float
    Racha: int
    ProgresoModulo1: int
    ProgresoModulo2: int
    ProgresoModulo3: int
    Total: int

@router.get("/home", response_model=HomeResponse)
async def get_home_data(
    current_user: dict = Depends(require_auth),
    db: Session = Depends(get_db)
):
    # Get user_id from the authenticated token
    user_id = current_user["userId"]
    
    user = db.query(Usuario).filter(Usuario.id_usuario == user_id).first()
    if not user:
        raise HTTPException(
            status_code=404,
            detail="Usuario no encontrado"
        )
    
    # Build days dict (placeholder - could be expanded with actual tracking)
    hoy = datetime.now().date()
    dias_semana = ["Lunes", "Martes", "Miercoles", "Jueves", "Viernes", "Sabado", "Domingo"]
    dias_dict = {dia: False for dia in dias_semana}
    
    # Get desafio for this user (using id_desafio as user reference)
    desafio = db.query(DesafioDiario).filter(
        DesafioDiario.id_desafio == user_id
    ).first()
    
    if desafio:
        misiones = desafio.lecciones_completadas or 0
    else:
        # Create desafio for user if not exists
        desafio = DesafioDiario(
            id_desafio=user_id,
            lecciones_completadas=0,
            modulos_completados=0,
            xp_ganado=0,
            nombre_desafio="Desafio diario"
        )
        db.add(desafio)
        db.commit()
        misiones = 0
    
    # Calculate racha (streak) - simplified version
    racha = 0
    if desafio and desafio.lecciones_completadas and desafio.lecciones_completadas > 0:
        racha = 1  # At least 1 day if has progress
    
    # Calculate overall progress (average of all modules)
    progreso_modulos = db.query(UsuarioModulo).filter(
        UsuarioModulo.id_usuario == user_id
    ).all()
    
    if progreso_modulos:
        progreso_total = sum(float(m.progreso_pct or 0) for m in progreso_modulos) / len(progreso_modulos)
    else:
        progreso_total = 0.0
    
    # Get progress for each of the 3 modules specifically
    modulo1 = db.query(UsuarioModulo).filter(
        UsuarioModulo.id_usuario == user_id,
        UsuarioModulo.id_modulo == 1
    ).first()
    
    modulo2 = db.query(UsuarioModulo).filter(
        UsuarioModulo.id_usuario == user_id,
        UsuarioModulo.id_modulo == 2
    ).first()
    
    modulo3 = db.query(UsuarioModulo).filter(
        UsuarioModulo.id_usuario == user_id,
        UsuarioModulo.id_modulo == 3
    ).first()
    
    progreso_modulo1 = int(float(modulo1.progreso_pct or 0)) if modulo1 else 0
    progreso_modulo2 = int(float(modulo2.progreso_pct or 0)) if modulo2 else 0
    progreso_modulo3 = int(float(modulo3.progreso_pct or 0)) if modulo3 else 0
    
    # Build response
    home_data = {
        "Usuario": user.to_dict(),
        "Dias": dias_dict,
        "Misiones": misiones,
        "Progreso": round(progreso_total, 1),
        "Racha": racha,
        "ProgresoModulo1": progreso_modulo1,
        "ProgresoModulo2": progreso_modulo2,
        "ProgresoModulo3": progreso_modulo3
    }

    return home_data