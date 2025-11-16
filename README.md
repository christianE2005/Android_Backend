# Python Backend API

Backend API desarrollado con **FastAPI** y **PostgreSQL** que incluye autenticación con Firebase y JWT.

## 🚀 Características

- 🔐 Autenticación con Firebase Authentication
- 🔑 Tokens JWT para sesiones
- 🗄️ Base de datos PostgreSQL con SQLAlchemy
- ⚡ FastAPI para alto rendimiento
- 🛡️ Middleware de seguridad
- 📝 Validación de datos con Pydantic

## 📋 Requisitos Previos

- Python 3.8 o superior
- PostgreSQL (o Supabase)
- Cuenta de Firebase con Authentication habilitado

## 🔧 Instalación

1. **Clonar el repositorio**
```bash
git clone <repository-url>
cd android-backend-api
```

2. **Crear entorno virtual**
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

3. **Instalar dependencias**
```bash
pip install -r requirements.txt
```

4. **Configurar variables de entorno**
```bash
cp .env.example .env
```

Edita el archivo `.env` con tus credenciales:
- `DATABASE_URL`: URL de conexión a PostgreSQL
- `JWT_SECRET`: Clave secreta para JWT (genera una segura)
- `GOOGLE_APPLICATION_CREDENTIALS`: Ruta al archivo JSON de Firebase
- `CORS_ORIGIN`: Origen permitido para CORS (usa `*` para desarrollo)

5. **Configurar Firebase**
   - Descarga tu archivo de credenciales de Firebase Admin SDK
   - Guárdalo de forma segura
   - Actualiza `GOOGLE_APPLICATION_CREDENTIALS` en `.env`

## 🏃‍♂️ Ejecutar la Aplicación

### Desarrollo
```bash
python main.py
```

O usando uvicorn directamente:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Producción
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

La API estará disponible en: `http://localhost:8000`

## 📚 Documentación API

FastAPI genera documentación automática:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🔌 Endpoints

### Health Check
```http
GET /health
```

### Autenticación
```http
POST /auth/login
Content-Type: application/json

{
  "firebaseToken": "firebase-id-token-here"
}
```

Respuesta:
```json
{
  "token": "jwt-token",
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "isAdmin": false
  }
}
```

### Endpoint Protegido
```http
GET /me
Authorization: Bearer <jwt-token>
```

Respuesta:
```json
{
  "userId": "uuid",
  "email": "user@example.com",
  "isAdmin": false
}
```

## 🏗️ Estructura del Proyecto

```
android-backend-api/
├── main.py                 # Punto de entrada de la aplicación
├── requirements.txt        # Dependencias Python
├── .env.example           # Plantilla de variables de entorno
├── database/
│   └── db.py              # Configuración de SQLAlchemy
├── models/
│   └── user.py            # Modelo de Usuario
├── routes/
│   └── auth_routes.py     # Rutas de autenticación
└── middleware/
    └── auth_middleware.py # Middleware de autenticación JWT
```

## 🧪 Testing

Para probar los endpoints puedes usar:
- **curl**
- **Postman**
- **Thunder Client** (VS Code extension)
- La interfaz de Swagger en `/docs`

## 🔒 Seguridad

- Los tokens JWT expiran en 1 hora
- Las contraseñas no se almacenan (autenticación delegada a Firebase)
- Conexión SSL requerida para la base de datos
- CORS configurado según variables de entorno

## 📝 Migración desde Node.js

Este proyecto fue convertido desde Node.js/Express a Python/FastAPI. Los cambios principales:

- **Express → FastAPI**: Framework web moderno con validación automática
- **Sequelize → SQLAlchemy**: ORM robusto para Python
- **jsonwebtoken → PyJWT**: Manejo de tokens JWT
- **firebase-admin**: Misma librería en Python
- **dotenv**: Mismo propósito, diferente implementación

## 🤝 Contribuir

1. Fork el proyecto
2. Crea una rama (`git checkout -b feature/nueva-caracteristica`)
3. Commit tus cambios (`git commit -am 'Agregar nueva característica'`)
4. Push a la rama (`git push origin feature/nueva-caracteristica`)
5. Abre un Pull Request

## 📄 Licencia

Este proyecto está bajo la licencia MIT.
