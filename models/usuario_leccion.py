from sqlalchemy import Column, Integer, Boolean, ForeignKey, DECIMAL, DateTime
from datetime import datetime
from database.db import Base


class UsuarioLeccion(Base):
    __tablename__ = "usuarios_lecciones"
    
    id_usuario = Column(Integer, ForeignKey("usuarios.id_usuario"), primary_key=True)
    id_leccion = Column(Integer, ForeignKey("lecciones.id_leccion"), primary_key=True)
    completado = Column(Boolean, default=False)
    intentos = Column(Integer, default=0)
    calificacion = Column(DECIMAL(5, 2))
    actualizado_en = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            "id_usuario": self.id_usuario,
            "id_leccion": self.id_leccion,
            "completado": bool(self.completado),
            "intentos": self.intentos,
            "calificacion": float(self.calificacion) if self.calificacion else None,
            "actualizado_en": self.actualizado_en.isoformat() if self.actualizado_en else None
        }
