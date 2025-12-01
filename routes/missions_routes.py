from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime

from database.db import get_db
from models.user import Usuario
from models.desafio_diario import DesafioDiario
from middleware.auth_middleware import require_auth

router = APIRouter()


# ============== SCHEMAS ==============

class MissionInfo(BaseModel):
    id: int
    nombre: str
    descripcion: str
    progreso_actual: int
    meta: int
    completada: bool
    xp_recompensa: int

class MissionsResponse(BaseModel):
    fecha: str
    misiones: list[MissionInfo]

class UpdateMissionRequest(BaseModel):
    mision_id: int
    progreso: int

class UpdateMissionResponse(BaseModel):
    mensaje: str
    mision_completada: bool
    xp_ganado: int


# ============== ENDPOINTS ==============

@router.get("/daily", response_model=MissionsResponse)
async def get_daily_missions(
    current_user: dict = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """
    Get today's daily missions with progress
    """
    user_id = current_user["userId"]
    
    # Get or create today's challenge record
    desafio = db.query(DesafioDiario).filter(
        DesafioDiario.id_desafio == user_id  # Using id_desafio as user reference
    ).first()
    
    if not desafio:
        desafio = DesafioDiario(
            id_desafio=user_id,
            lecciones_completadas=0,
            modulos_completados=0,
            xp_ganado=0
        )
        db.add(desafio)
        db.commit()
        db.refresh(desafio)
    
    # Define the 3 daily missions based on your schema
    misiones = [
        MissionInfo(
            id=1,
            nombre="Completa 3 lecciones",
            descripcion="Termina 3 lecciones de cualquier modulo",
            progreso_actual=min(desafio.lecciones_completadas or 0, 3),
            meta=3,
            completada=(desafio.lecciones_completadas or 0) >= 3,
            xp_recompensa=50
        ),
        MissionInfo(
            id=2,
            nombre="Completa 1 modulo",
            descripcion="Termina todas las lecciones de un modulo",
            progreso_actual=min(desafio.modulos_completados or 0, 1),
            meta=1,
            completada=(desafio.modulos_completados or 0) >= 1,
            xp_recompensa=100
        ),
        MissionInfo(
            id=3,
            nombre="Gana 100 XP",
            descripcion="Acumula 100 puntos de experiencia",
            progreso_actual=min(desafio.xp_ganado or 0, 100),
            meta=100,
            completada=(desafio.xp_ganado or 0) >= 100,
            xp_recompensa=25
        )
    ]
    
    return MissionsResponse(
        fecha=datetime.now().strftime("%Y-%m-%d"),
        misiones=misiones
    )


@router.post("/update", response_model=UpdateMissionResponse)
async def update_mission(
    request: UpdateMissionRequest,
    current_user: dict = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """
    Update a mission's progress
    """
    user_id = current_user["userId"]
    
    # Get or create challenge record
    desafio = db.query(DesafioDiario).filter(
        DesafioDiario.id_desafio == user_id
    ).first()
    
    if not desafio:
        desafio = DesafioDiario(
            id_desafio=user_id,
            lecciones_completadas=0,
            modulos_completados=0,
            xp_ganado=0
        )
        db.add(desafio)
    
    xp_ganado = 0
    mision_completada = False
    
    # Update based on mission_id
    if request.mision_id == 1:
        # Lecciones completadas
        desafio.lecciones_completadas = request.progreso
        if request.progreso >= 3:
            mision_completada = True
            xp_ganado = 50
    elif request.mision_id == 2:
        # Modulos completados
        desafio.modulos_completados = request.progreso
        if request.progreso >= 1:
            mision_completada = True
            xp_ganado = 100
    elif request.mision_id == 3:
        # XP ganado
        desafio.xp_ganado = request.progreso
        if request.progreso >= 100:
            mision_completada = True
            xp_ganado = 25
    else:
        raise HTTPException(status_code=400, detail="Mision no valida")
    
    desafio.actualizado_en = datetime.utcnow()
    
    # Add XP reward to user if mission completed
    if mision_completada and xp_ganado > 0:
        user = db.query(Usuario).filter(Usuario.id_usuario == user_id).first()
        if user:
            user.monedas = (user.monedas or 0) + xp_ganado
    
    db.commit()
    
    return UpdateMissionResponse(
        mensaje="Mision actualizada" if not mision_completada else "¡Mision completada!",
        mision_completada=mision_completada,
        xp_ganado=xp_ganado
    )
