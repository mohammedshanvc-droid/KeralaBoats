
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session, selectinload

from app.database import get_database
from app.models import Houseboat, User
from app.security import decode_access_token


router = APIRouter(
    prefix="/api/houseboats",
    tags=["Houseboat JSON API"]
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")


def get_current_admin(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_database)
):
    payload = decode_access_token(token)

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"}
        )

    user_id = payload.get("sub")

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"}
        )

    user = db.get(User, int(user_id))

    if not user or user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required."
        )

    return user


def houseboat_response(houseboat: Houseboat):
    return {
        "id": houseboat.id,
        "name": houseboat.name,
        "location": houseboat.location,
        "description": houseboat.description,
        "facilities": houseboat.facilities,
        "bedrooms": houseboat.bedrooms,
        "capacity": houseboat.capacity,
        "price_per_night": houseboat.price_per_night,
        "food_available": houseboat.food_available,
        "meal_options": houseboat.meal_options,
        "food_menu": houseboat.food_menu,
        "special_food": houseboat.special_food,
        "is_active": houseboat.is_active,
        "images": [
            {
                "id": image.id,
                "image_path": image.image_path,
                "is_primary": image.is_primary
            }
            for image in houseboat.images
        ]
    }


@router.get("/")
def get_all_houseboats(
    db: Session = Depends(get_database),
    current_admin: User = Depends(get_current_admin)
):
    houseboats = (
        db.query(Houseboat)
        .options(selectinload(Houseboat.images))
        .order_by(Houseboat.id.desc())
        .all()
    )

    return {
        "message": "Houseboats retrieved successfully",
        "count": len(houseboats),
        "houseboats": [
            houseboat_response(houseboat)
            for houseboat in houseboats
        ]
    }


@router.get("/{houseboat_id}")
def get_houseboat_by_id(
    houseboat_id: int,
    db: Session = Depends(get_database),
    current_admin: User = Depends(get_current_admin)
):
    houseboat = (
        db.query(Houseboat)
        .options(selectinload(Houseboat.images))
        .filter(Houseboat.id == houseboat_id)
        .first()
    )

    if not houseboat:
        raise HTTPException(
            status_code=404,
            detail="Houseboat not found."
        )

    return {
        "message": "Houseboat retrieved successfully",
        "houseboat": houseboat_response(houseboat)
    }
