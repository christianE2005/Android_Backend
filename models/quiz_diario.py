from sqlalchemy import Column, Integer, Boolean, ForeignKey, Date, DateTime, DECIMAL
from datetime import datetime
from database.db import Base


class QuizDiario(Base):
    __tablename__ = "quizzes_diarios"
    
    id_quiz = Column(Integer, primary_key=True, autoincrement=True)
    id_usuario = Column(Integer, ForeignKey("usuarios.id_usuario"), nullable=False)
    fecha_dia = Column(Date, nullable=False)
    completado = Column(Boolean, default=False)
    calificacion = Column(DECIMAL(5, 2))
    creado_en = Column(DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            "id_quiz": self.id_quiz,
            "id_usuario": self.id_usuario,
            "fecha_dia": self.fecha_dia.isoformat() if self.fecha_dia else None,
            "completado": bool(self.completado),
            "calificacion": float(self.calificacion) if self.calificacion else None,
            "creado_en": self.creado_en.isoformat() if self.creado_en else None
        }
