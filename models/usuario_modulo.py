from sqlalchemy import Column, Integer, Boolean, ForeignKey, DECIMAL, DateTime
from datetime import datetime
from database.db import Base


class UsuarioModulo(Base):
    __tablename__ = "usuarios_modulos"
    
    id_usuario = Column(Integer, ForeignKey("usuarios.id_usuario"), primary_key=True)
    id_modulo = Column(Integer, ForeignKey("modulos.id_modulo"), primary_key=True)
    progreso_pct = Column(DECIMAL(5, 2), default=0.00)
    completado = Column(Boolean, default=False)
    actualizado_en = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            "id_usuario": self.id_usuario,
            "id_modulo": self.id_modulo,
            "progreso_pct": float(self.progreso_pct) if self.progreso_pct else 0.0,
            "completado": bool(self.completado),
            "actualizado_en": self.actualizado_en.isoformat() if self.actualizado_en else None
        }
