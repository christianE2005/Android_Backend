from sqlalchemy import Column, Integer, String, Boolean
from database.db import Base


class Modulo(Base):
    __tablename__ = "modulos"
    
    id_modulo = Column(Integer, primary_key=True, autoincrement=True)
    titulo = Column(String(150), nullable=False)
    orden = Column(Integer, nullable=False)
    activo = Column(Boolean, default=True)
    
    def to_dict(self):
        return {
            "id_modulo": self.id_modulo,
            "titulo": self.titulo,
            "orden": self.orden,
            "activo": bool(self.activo)
        }
