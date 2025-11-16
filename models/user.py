import os
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime
from database.db import Base
from fastapi import HTTPException
import re


class Usuario(Base):
    __tablename__ = "usuarios"
    # Only use schema for PostgreSQL, not for SQLite or MySQL
    db_url = os.getenv("DATABASE_URL", "")
    __table_args__ = {"schema": "public"} if db_url.startswith("postgresql") else {}
    
    id_usuario = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
        nullable=False
    )
    correo = Column(
        String(255),
        unique=True,
        nullable=False,
        index=True
    )
    contrasena_hash = Column(
        String(255),
        nullable=False
    )
    nombre = Column(
        String(255),
        nullable=False
    )
    creado_en = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow
    )

    def to_dict(self):
        """Convert usuario to dictionary"""
        return {
            "id_usuario": self.id_usuario,
            "correo": self.correo,
            "nombre": self.nombre,
            "creado_en": self.creado_en.isoformat() if self.creado_en else None
        }
