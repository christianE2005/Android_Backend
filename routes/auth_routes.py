import os
import re
import jwt
import bcrypt
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
import firebase_admin
from firebase_admin import credentials, auth

from database.db import get_db
from models.user import Usuario

router = APIRouter()

# Initialize Firebase Admin (using Application Default Credentials or service account)
if not firebase_admin._apps:
    try:
        # Try to use Application Default Credentials
        firebase_admin.initialize_app(
            credentials.ApplicationDefault()
        )
    except Exception as e:
        print(f"Warning: Firebase initialization failed: {e}")
        print("Make sure GOOGLE_APPLICATION_CREDENTIALS is set")


class SignupRequest(BaseModel):
    correo: str
    contrasena: str
    nombre: str


class LoginRequest(BaseModel):
    correo: str
    contrasena: str


class FirebaseLoginRequest(BaseModel):
    firebaseToken: str


class AuthResponse(BaseModel):
    token: str
    usuario: dict


@router.post("/signup", response_model=AuthResponse)
async def signup(request: SignupRequest, db: Session = Depends(get_db)):
    """
    Sign up endpoint - creates a new user account
    """
    try:
        # 1. Check if user already exists
        existing_user = db.query(Usuario).filter(Usuario.correo == request.correo).first()
        if existing_user:
            raise HTTPException(
                status_code=400,
                detail="El correo ya está registrado"
            )
        
        # 2. Validate password length
        if len(request.contrasena) < 6:
            raise HTTPException(
                status_code=400,
                detail="La contraseña debe tener al menos 6 caracteres"
            )
        # 2. Validate email format

        def es_correo_valido(email: str) -> bool:
            regex = r'^[\w\.-]+@([\w-]+\.)+[a-zA-Z]{2,}$'
            return re.match(regex, email) is not None
        if not es_correo_valido(request.correo):
            raise HTTPException(
                status_code=400,
                detail="El correo no tiene un formato válido"
            )
        # 3. Hash password
        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw(request.contrasena.encode('utf-8'), salt)
        
        # 4. Create new user
        nuevo_usuario = Usuario(
            correo=request.correo,
            contrasena_hash=hashed_password.decode('utf-8'),
            nombre=request.nombre,
            creado_en=datetime.utcnow()
        )
        
        db.add(nuevo_usuario)
        db.commit()
        db.refresh(nuevo_usuario)
        
        # 5. Create JWT token
        jwt_secret = os.getenv("JWT_SECRET")
        if not jwt_secret:
            raise HTTPException(
                status_code=500,
                detail="JWT_SECRET not configured"
            )
        
        token_payload = {
            "userId": nuevo_usuario.id_usuario,
            "correo": nuevo_usuario.correo,
            "nombre": nuevo_usuario.nombre,
            "exp": datetime.utcnow() + timedelta(hours=24)  # 24 hours expiration
        }
        
        token = jwt.encode(
            token_payload,
            jwt_secret,
            algorithm="HS256"
        )
        
        # 6. Return response
        return AuthResponse(
            token=token,
            usuario=nuevo_usuario.to_dict()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"Signup error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error al crear cuenta: {str(e)}"
        )


@router.post("/login", response_model=AuthResponse)
async def login(request: LoginRequest, db: Session = Depends(get_db)):
    """
    Login endpoint - authenticates user with email and password
    """
    try:
        # 1. Find user by email
        usuario = db.query(Usuario).filter(Usuario.correo == request.correo).first()
        
        if not usuario:
            raise HTTPException(
                status_code=401,
                detail="Correo o contraseña incorrectos"
            )
        
        # 2. Verify password
        if not bcrypt.checkpw(request.contrasena.encode('utf-8'), usuario.contrasena_hash.encode('utf-8')):
            raise HTTPException(
                status_code=401,
                detail="Correo o contraseña incorrectos"
            )
        
        # 3. Create JWT token
        jwt_secret = os.getenv("JWT_SECRET")
        if not jwt_secret:
            raise HTTPException(
                status_code=500,
                detail="JWT_SECRET not configured"
            )
        
        token_payload = {
            "userId": usuario.id_usuario,
            "correo": usuario.correo,
            "nombre": usuario.nombre,
            "exp": datetime.utcnow() + timedelta(hours=24)  # 24 hours expiration
        }
        
        token = jwt.encode(
            token_payload,
            jwt_secret,
            algorithm="HS256"
        )
        
        # 4. Return response
        return AuthResponse(
            token=token,
            usuario=usuario.to_dict()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Login error: {e}")
        raise HTTPException(
            status_code=401,
            detail="Error al iniciar sesión"
        )


@router.post("/login/firebase", response_model=AuthResponse)
async def firebase_login(request: FirebaseLoginRequest, db: Session = Depends(get_db)):
    """
    Firebase login endpoint - verifies Firebase token and creates/updates user
    """
    try:
        if not request.firebaseToken:
            raise HTTPException(
                status_code=400,
                detail="firebaseToken is required"
            )
        
        # 1. Verify Firebase ID token
        try:
            decoded_token = auth.verify_id_token(request.firebaseToken)
        except Exception as e:
            raise HTTPException(
                status_code=401,
                detail=f"Invalid Firebase token: {str(e)}"
            )
        
        email = decoded_token.get("email")
        nombre = decoded_token.get("name", email.split('@')[0])
        
        if not email:
            raise HTTPException(
                status_code=400,
                detail="No email in token"
            )
        
        # 2. Find or create user
        usuario = db.query(Usuario).filter(Usuario.correo == email).first()
        
        if not usuario:
            # Create new user with Firebase authentication
            # Generate a random password hash since Firebase handles auth
            salt = bcrypt.gensalt()
            temp_password = bcrypt.hashpw(os.urandom(32), salt)
            
            usuario = Usuario(
                correo=email,
                contrasena_hash=temp_password.decode('utf-8'),
                nombre=nombre,
                creado_en=datetime.utcnow()
            )
            db.add(usuario)
            db.commit()
            db.refresh(usuario)
        
        # 3. Create JWT token
        jwt_secret = os.getenv("JWT_SECRET")
        if not jwt_secret:
            raise HTTPException(
                status_code=500,
                detail="JWT_SECRET not configured"
            )
        
        token_payload = {
            "userId": usuario.id_usuario,
            "correo": usuario.correo,
            "nombre": usuario.nombre,
            "exp": datetime.utcnow() + timedelta(hours=24)
        }
        
        token = jwt.encode(
            token_payload,
            jwt_secret,
            algorithm="HS256"
        )
        
        # 4. Return response
        return AuthResponse(
            token=token,
            usuario=usuario.to_dict()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"Firebase login error: {e}")
        raise HTTPException(
            status_code=401,
            detail="Invalid Firebase token"
        )
