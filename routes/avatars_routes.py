from fastapi import APIRouter, Depends
from pydantic import BaseModel

from middleware.auth_middleware import require_auth

router = APIRouter()


# ============== SCHEMAS ==============

class AvatarInfo(BaseModel):
    id: int
    nombre: str
    url: str

class AvatarsResponse(BaseModel):
    total: int
    avatares: list[AvatarInfo]


# ============== STATIC AVATARS LIST ==============
# Since there's no avatars table, we define them here
AVATARES = [
    AvatarInfo(id=1, nombre="Tigre", url="https://example.com/avatars/tigre.png"),
    AvatarInfo(id=2, nombre="Leon", url="https://example.com/avatars/leon.png"),
    AvatarInfo(id=3, nombre="Aguila", url="https://example.com/avatars/aguila.png"),
    AvatarInfo(id=4, nombre="Oso", url="https://example.com/avatars/oso.png"),
    AvatarInfo(id=5, nombre="Lobo", url="https://example.com/avatars/lobo.png"),
    AvatarInfo(id=6, nombre="Panda", url="https://example.com/avatars/panda.png"),
    AvatarInfo(id=7, nombre="Gato", url="https://example.com/avatars/gato.png"),
    AvatarInfo(id=8, nombre="Perro", url="https://example.com/avatars/perro.png"),
    AvatarInfo(id=9, nombre="Conejo", url="https://example.com/avatars/conejo.png"),
    AvatarInfo(id=10, nombre="Zorro", url="https://example.com/avatars/zorro.png"),
]


# ============== ENDPOINTS ==============

@router.get("/", response_model=AvatarsResponse)
async def get_avatars(
    current_user: dict = Depends(require_auth)
):
    """
    Get list of available avatars
    """
    return AvatarsResponse(
        total=len(AVATARES),
        avatares=AVATARES
    )
