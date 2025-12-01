from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from database.db import Base


class Leccion(Base):
    __tablename__ = "lecciones"
    
    id_leccion = Column(Integer, primary_key=True, autoincrement=True)
    id_modulo = Column(Integer, ForeignKey("modulos.id_modulo"), nullable=False)
    titulo = Column(String(150), nullable=False)
    orden = Column(Integer, nullable=False)
    activo = Column(Boolean, default=True)
    
    def to_dict(self):
        return {
            "id_leccion": self.id_leccion,
            "id_modulo": self.id_modulo,
            "titulo": self.titulo,
            "orden": self.orden,
            "activo": bool(self.activo)
        }
