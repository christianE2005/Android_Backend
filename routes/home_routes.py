from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta

from database.db import get_db
from models.user import Usuario
from models.desafio_diario import DesafioDiario
from models.usuario_modulo import UsuarioModulo
from models.usuario_leccion import UsuarioLeccion
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
    
    # Calculate days of the current week where user had activity
    hoy = datetime.now().date()
    # Get the Monday of the current week
    inicio_semana = hoy - timedelta(days=hoy.weekday())
    fin_semana = inicio_semana + timedelta(days=6)
    
    # Get all user lesson completions this week
    actividad_semana = db.query(UsuarioLeccion).filter(
        UsuarioLeccion.id_usuario == user_id,
        UsuarioLeccion.completado == True,
        UsuarioLeccion.actualizado_en >= datetime.combine(inicio_semana, datetime.min.time()),
        UsuarioLeccion.actualizado_en <= datetime.combine(fin_semana, datetime.max.time())
    ).all()
    
    # Map weekday numbers to Spanish names (Monday=0, Sunday=6)
    dias_map = {0: "Lunes", 1: "Martes", 2: "Miercoles", 3: "Jueves", 4: "Viernes", 5: "Sabado", 6: "Domingo"}
    dias_dict = {dia: False for dia in dias_map.values()}
    
    # Mark days where user had activity
    dias_activos = set()
    for actividad in actividad_semana:
        if actividad.actualizado_en:
            dia_num = actividad.actualizado_en.weekday()
            dia_nombre = dias_map[dia_num]
            dias_dict[dia_nombre] = True
            dias_activos.add(actividad.actualizado_en.date())
    
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
    
    # Calculate racha (streak) - count consecutive days backwards from today
    racha = 0
    fecha_check = hoy
    while True:
        # Check if user had activity on this day
        actividad_dia = db.query(UsuarioLeccion).filter(
            UsuarioLeccion.id_usuario == user_id,
            UsuarioLeccion.completado == True,
            func.date(UsuarioLeccion.actualizado_en) == fecha_check
        ).first()
        
        if actividad_dia:
            racha += 1
            fecha_check -= timedelta(days=1)
        else:
            # If no activity today but checking today, try yesterday
            if fecha_check == hoy:
                fecha_check -= timedelta(days=1)
                continue
            break
        
        # Safety limit to avoid infinite loop
        if racha > 365:
            break
    
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
    
    # Count total lessons completed by user
    total_lecciones = db.query(UsuarioLeccion).filter(
        UsuarioLeccion.id_usuario == user_id,
        UsuarioLeccion.completado == True
    ).count()
    
    # Build response
    home_data = {
        "Usuario": user.to_dict(),
        "Dias": dias_dict,
        "Misiones": misiones,
        "Progreso": round(progreso_total, 1),
        "Racha": racha,
        "ProgresoModulo1": progreso_modulo1,
        "ProgresoModulo2": progreso_modulo2,
        "ProgresoModulo3": progreso_modulo3,
        "Total": total_lecciones
    }

    return home_data