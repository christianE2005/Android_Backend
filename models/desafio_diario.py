from sqlalchemy import Column, Integer, DateTime
from datetime import datetime
from database.db import Base


class DesafioDiario(Base):
    __tablename__ = "desafios_diarios"
    
    id_desafio = Column(Integer, primary_key=True, autoincrement=True)
    lecciones_completadas = Column(Integer, default=0)
    modulos_completados = Column(Integer, default=0)
    xp_ganado = Column(Integer, default=0)
    actualizado_en = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            "id_desafio": self.id_desafio,
            "lecciones_completadas": self.lecciones_completadas,
            "modulos_completados": self.modulos_completados,
            "xp_ganado": self.xp_ganado,
            "actualizado_en": self.actualizado_en.isoformat() if self.actualizado_en else None
        }
