from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from database.db import Base


class Video(Base):
    __tablename__ = "videos"
    
    id_video = Column(Integer, primary_key=True, autoincrement=True)
    id_leccion = Column(Integer, ForeignKey("lecciones.id_leccion"), nullable=False)
    titulo = Column(String(150), nullable=False)
    url = Column(String(500), nullable=False)
    duracion_seg = Column(Integer)
    orden = Column(Integer, nullable=False)
    activo = Column(Boolean, default=True)
    
    def to_dict(self):
        return {
            "id_video": self.id_video,
            "id_leccion": self.id_leccion,
            "titulo": self.titulo,
            "url": self.url,
            "duracion_seg": self.duracion_seg,
            "orden": self.orden,
            "activo": bool(self.activo)
        }
