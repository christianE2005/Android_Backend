from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
import firebase_admin
from firebase_admin import credentials, auth

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
    Mision1: int
    Mision2: int
    Mision3: int
    Progreso: float
    Racha: int
    ProgresoModulo1: int
    ProgresoModulo2: int
    ProgresoModulo3: int

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
    hoy = datetime.now().date()
    dias_semana = ["Lunes", "Martes", "Miercoles", "Jueves", "Viernes", "Sabado", "Domingo"]
    dias_dict = {}

    dia_actual = hoy.weekday()

    inicio_semana = hoy -  timedelta(days=dia_actual)

    desafios_semana = db.query(DesafioDiario).filter(
        DesafioDiario.id_usuario == user_id,
        DesafioDiario.fecha_dia >= inicio_semana,
        DesafioDiario.fecha_dia <= hoy
    ).all()
    
    desafios_completados = {d.fecha_dia: d.completado for d in desafios_semana}
    
    for i, dia_nombre in enumerate(dias_semana):
        fecha_dia = inicio_semana + timedelta(days=i)
        if fecha_dia <= hoy:
            dias_dict[dia_nombre] = bool(desafios_completados.get(fecha_dia, False))
        else:
            dias_dict[dia_nombre] = False
    
    desafio_hoy = db.query(DesafioDiario).filter(
        DesafioDiario.id_usuario == user_id,
        DesafioDiario.fecha_dia == hoy
    ).first()
    
    if desafio_hoy:
        misiones = desafio_hoy.lecciones_completadas
        
    else:
        desafio_hoy = DesafioDiario(
            id_usuario=user_id,
            fecha_dia=hoy,
            lecciones_completadas=0,
            modulos_completados=0,
            xp_ganado=0,
            completado=False
        )
        db.add(desafio_hoy)
        db.commit()
        misiones = 0
    
    # 4. Calculate current streak (racha)
    racha = 0
    fecha_check = hoy
    while True:
        desafio = db.query(DesafioDiario).filter(
            DesafioDiario.id_usuario == user_id,
            DesafioDiario.fecha_dia == fecha_check
        ).first()
        
        if desafio and desafio.completado:
            racha += 1
            fecha_check -= timedelta(days=1)
        else:
            break
    
    # 5. Calculate overall progress (average of all modules)
    progreso_modulos = db.query(UsuarioModulo).filter(
        UsuarioModulo.id_usuario == user_id
    ).all()
    
    if progreso_modulos:
        progreso_total = sum(float(m.progreso_pct or 0) for m in progreso_modulos) / len(progreso_modulos)
    else:
        progreso_total = 0.0
    
    # 6. Get progress for each of the 3 modules specifically
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
    
    # 7. Build response
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