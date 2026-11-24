import io
import os
import uuid

from fastapi import APIRouter, Request, Depends, Form, File, UploadFile
from fastapi.responses import RedirectResponse
from PIL import Image
from sqlalchemy.orm import Session, selectinload

from app.templating import templates
from app.database import get_database
from app.models import (
    Houseboat,
    HouseboatImage,
    Destination,
    DestinationImage
)

router = APIRouter(
    prefix="/admin",
    tags=["Admin"]
)

UPLOAD_FOLDER = "app/static/uploads"
ALLOWED_EXTENSIONS = [".jpg", ".jpeg", ".png", ".webp"]
MAX_IMAGE_SIZE = 5 * 1024 * 1024


def validate_image_contents(contents: bytes):
    if len(contents) > MAX_IMAGE_SIZE:
        raise ValueError("Each image must be 5 MB or smaller.")

    try:
        Image.open(io.BytesIO(contents)).verify()
    except Exception:
        raise ValueError("One of the files is not a valid image.")


def check_admin(request: Request):
    user = request.session.get("user")

    if not user or user.get("role") != "admin":
        return None

    return user


def admin_redirect(request: Request):
    if not request.session.get("user"):
        return RedirectResponse("/login", status_code=303)

    return RedirectResponse("/houseboats", status_code=303)


def save_image(
    image: UploadFile,
    houseboat_id: int,
    is_primary: bool,
    db: Session
):
    extension = os.path.splitext(image.filename)[1].lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise ValueError("Only JPG, JPEG, PNG and WEBP images are allowed.")

    filename = f"{uuid.uuid4().hex}{extension}"
    file_path = os.path.join(UPLOAD_FOLDER, filename)

    contents = image.file.read()

    if not contents:
        raise ValueError("One of the uploaded images is empty.")

    validate_image_contents(contents)

    with open(file_path, "wb") as file:
        file.write(contents)

    db.add(
        HouseboatImage(
            houseboat_id=houseboat_id,
            image_path=filename,
            is_primary=is_primary
        )
    )

    return file_path


@router.get("/")
def admin_home():
    return RedirectResponse("/admin/dashboard", status_code=303)


@router.get("/dashboard")
async def admin_dashboard(request: Request):

    user = check_admin(request)

    if not user:
        return admin_redirect(request)

    return templates.TemplateResponse(
        request=request,
        name="admin_dashboard.html",
        context={"user": user}
    )


@router.get("/add-houseboat")
async def add_houseboat_page(request: Request):

    user = check_admin(request)

    if not user:
        return admin_redirect(request)

    return templates.TemplateResponse(
        request=request,
        name="add_houseboat.html",
        context={
            "user": user,
            "error": None
        }
    )


@router.post("/add-houseboat")
async def create_houseboat(
    request: Request,
    name: str = Form(...),
    location: str = Form(...),
    description: str = Form(...),
    facilities: str = Form(...),
    bedrooms: int = Form(...),
    capacity: int = Form(...),
    price_per_night: float = Form(...),
    food_available: str = Form(...),
    meal_options: str = Form(""),
    food_menu: str = Form(""),
    special_food: str = Form(""),
    images: list[UploadFile] = File(...),
    db: Session = Depends(get_database)
):

    user = check_admin(request)

    if not user:
        return admin_redirect(request)

    if bedrooms < 1 or capacity < 1 or price_per_night <= 0:
        return templates.TemplateResponse(
            request=request,
            name="add_houseboat.html",
            context={
                "user": user,
                "error": "Please enter valid bedrooms, capacity and price."
            },
            status_code=400
        )

    valid_images = [
        image for image in images
        if image.filename
        and image.content_type
        and image.content_type.startswith("image/")
    ]

    if not valid_images:
        return templates.TemplateResponse(
            request=request,
            name="add_houseboat.html",
            context={
                "user": user,
                "error": "Please upload at least one valid image."
            },
            status_code=400
        )

    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    saved_files = []

    try:
        houseboat = Houseboat(
            name=name,
            location=location,
            description=description,
            facilities=facilities,
            bedrooms=bedrooms,
            capacity=capacity,
            price_per_night=price_per_night,
            food_available=food_available,
            meal_options=meal_options,
            food_menu=food_menu,
            special_food=special_food,
            is_active=True
        )

        db.add(houseboat)
        db.flush()

        for index, image in enumerate(valid_images):
            saved_files.append(
                save_image(image, houseboat.id, index == 0, db)
            )

        db.commit()

        return RedirectResponse(
            "/admin/houseboats",
            status_code=303
        )

    except Exception as error:
        db.rollback()

        for file_path in saved_files:
            if os.path.exists(file_path):
                os.remove(file_path)

        if isinstance(error, ValueError):
            message = str(error)
        else:
            message = "Could not add the houseboat. Check the details and photos."

        return templates.TemplateResponse(
            request=request,
            name="add_houseboat.html",
            context={
                "user": user,
                "error": message
            },
            status_code=400
        )

    finally:
        for image in images:
            await image.close()


@router.get("/houseboats")
async def view_houseboats(
    request: Request,
    db: Session = Depends(get_database)
):

    user = check_admin(request)

    if not user:
        return admin_redirect(request)

    houseboats = (
        db.query(Houseboat)
        .options(selectinload(Houseboat.images))
        .order_by(Houseboat.created_at.desc())
        .all()
    )

    return templates.TemplateResponse(
        request=request,
        name="admin_houseboats.html",
        context={
            "user": user,
            "houseboats": houseboats
        }
    )


@router.get("/houseboats/{houseboat_id}")
async def view_houseboat_details(
    houseboat_id: int,
    request: Request,
    db: Session = Depends(get_database)
):

    user = check_admin(request)

    if not user:
        return admin_redirect(request)

    houseboat = (
        db.query(Houseboat)
        .options(selectinload(Houseboat.images))
        .filter(Houseboat.id == houseboat_id)
        .first()
    )

    if not houseboat:
        return RedirectResponse(
            "/admin/houseboats",
            status_code=303
        )

    return templates.TemplateResponse(
        request=request,
        name="admin_houseboat_details.html",
        context={
            "user": user,
            "houseboat": houseboat
        }
    )


@router.get("/houseboats/{houseboat_id}/edit")
async def edit_houseboat_page(
    houseboat_id: int,
    request: Request,
    db: Session = Depends(get_database)
):

    user = check_admin(request)

    if not user:
        return admin_redirect(request)

    houseboat = (
        db.query(Houseboat)
        .options(selectinload(Houseboat.images))
        .filter(Houseboat.id == houseboat_id)
        .first()
    )

    if not houseboat:
        return RedirectResponse(
            "/admin/houseboats",
            status_code=303
        )

    return templates.TemplateResponse(
        request=request,
        name="edit_houseboat.html",
        context={
            "user": user,
            "houseboat": houseboat,
            "error": None
        }
    )


@router.post("/houseboats/{houseboat_id}/edit")
async def update_houseboat(
    houseboat_id: int,
    request: Request,
    name: str = Form(...),
    location: str = Form(...),
    description: str = Form(...),
    facilities: str = Form(...),
    bedrooms: int = Form(...),
    capacity: int = Form(...),
    price_per_night: float = Form(...),
    food_available: str = Form(""),
    meal_options: str = Form(""),
    food_menu: str = Form(""),
    special_food: str = Form(""),
    images: list[UploadFile] = File(default=[]),
    db: Session = Depends(get_database)
):

    user = check_admin(request)

    if not user:
        return admin_redirect(request)

    houseboat = (
        db.query(Houseboat)
        .options(selectinload(Houseboat.images))
        .filter(Houseboat.id == houseboat_id)
        .first()
    )

    if not houseboat:
        return RedirectResponse(
            "/admin/houseboats",
            status_code=303
        )

    saved_files = []

    try:
        if bedrooms < 1 or capacity < 1 or price_per_night <= 0:
            raise ValueError(
                "Please enter valid bedrooms, capacity and price."
            )

        houseboat.name = name
        houseboat.location = location
        houseboat.description = description
        houseboat.facilities = facilities
        houseboat.bedrooms = bedrooms
        houseboat.capacity = capacity
        houseboat.price_per_night = price_per_night
        houseboat.food_available = food_available
        houseboat.meal_options = meal_options
        houseboat.food_menu = food_menu
        houseboat.special_food = special_food

        valid_images = [
            image for image in images
            if image.filename
            and image.content_type
            and image.content_type.startswith("image/")
        ]

        os.makedirs(UPLOAD_FOLDER, exist_ok=True)

        for image in valid_images:
            is_primary = len(houseboat.images) == 0

            saved_files.append(
                save_image(image, houseboat.id, is_primary, db)
            )

        db.commit()

        return RedirectResponse(
            "/admin/houseboats",
            status_code=303
        )

    except Exception as error:
        db.rollback()

        for file_path in saved_files:
            if os.path.exists(file_path):
                os.remove(file_path)

        return templates.TemplateResponse(
            request=request,
            name="edit_houseboat.html",
            context={
                "user": user,
                "houseboat": houseboat,
                "error": str(error)
            },
            status_code=400
        )

    finally:
        for image in images:
            await image.close()


@router.post("/houseboats/{houseboat_id}/delete")
async def delete_houseboat(
    houseboat_id: int,
    request: Request,
    db: Session = Depends(get_database)
):

    user = check_admin(request)

    if not user:
        return admin_redirect(request)

    houseboat = (
        db.query(Houseboat)
        .options(
            selectinload(Houseboat.images),
            selectinload(Houseboat.bookings)
        )
        .filter(Houseboat.id == houseboat_id)
        .first()
    )

    if not houseboat:
        return RedirectResponse(
            "/admin/houseboats",
            status_code=303
        )

    if houseboat.bookings:
        return RedirectResponse(
            "/admin/houseboats?error=has_bookings",
            status_code=303
        )

    image_paths = [
        os.path.join(UPLOAD_FOLDER, image.image_path)
        for image in houseboat.images
    ]

    try:
        db.delete(houseboat)
        db.commit()

        for file_path in image_paths:
            if os.path.exists(file_path):
                os.remove(file_path)

    except Exception:
        db.rollback()

        return RedirectResponse(
            "/admin/houseboats?error=delete_failed",
            status_code=303
        )

    return RedirectResponse(
        "/admin/houseboats",
        status_code=303
    )


@router.get("/destinations")
def manage_destinations(
    request: Request,
    db: Session = Depends(get_database)
):

    user = check_admin(request)

    if not user:
        return admin_redirect(request)

    destinations = (
        db.query(Destination)
        .options(selectinload(Destination.images))
        .order_by(Destination.id.desc())
        .all()
    )

    return templates.TemplateResponse(
        request=request,
        name="destination.html",
        context={
            "user": user,
            "destinations": destinations
        }
    )


@router.post("/destinations/add")
async def add_destination(
    request: Request,
    name: str = Form(...),
    location: str = Form(...),
    description: str = Form(""),
    images: list[UploadFile] = File(default=[]),
    db: Session = Depends(get_database)
):

    user = check_admin(request)

    if not user:
        return admin_redirect(request)

    destination = Destination(
        name=name,
        location=location,
        description=description
    )

    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    saved_files = []

    try:
        db.add(destination)
        db.flush()

        for image in images:

            if not image.filename:
                continue

            extension = os.path.splitext(image.filename)[1].lower()

            if extension not in ALLOWED_EXTENSIONS:
                raise ValueError(
                    "Only JPG, JPEG, PNG and WEBP images are allowed."
                )

            contents = await image.read()

            if not contents:
                raise ValueError("An uploaded image is empty.")

            validate_image_contents(contents)

            filename = f"{uuid.uuid4().hex}{extension}"
            file_path = os.path.join(UPLOAD_FOLDER, filename)

            with open(file_path, "wb") as file:
                file.write(contents)

            saved_files.append(file_path)

            db.add(
                DestinationImage(
                    destination_id=destination.id,
                    image_path=filename
                )
            )

        db.commit()

        return RedirectResponse(
            "/admin/destinations",
            status_code=303
        )

    except Exception as error:
        db.rollback()

        for file_path in saved_files:
            if os.path.exists(file_path):
                os.remove(file_path)

        destinations = (
            db.query(Destination)
            .options(selectinload(Destination.images))
            .order_by(Destination.id.desc())
            .all()
        )

        return templates.TemplateResponse(
            request=request,
            name="destination.html",
            context={
                "user": user,
                "destinations": destinations,
                "error": str(error)
            },
            status_code=400
        )

    finally:
        for image in images:
            await image.close()


@router.post("/destinations/{destination_id}/delete")
def delete_destination(
    destination_id: int,
    request: Request,
    db: Session = Depends(get_database)
):

    user = check_admin(request)

    if not user:
        return admin_redirect(request)

    destination = (
        db.query(Destination)
        .options(selectinload(Destination.images))
        .filter(Destination.id == destination_id)
        .first()
    )

    if not destination:
        return RedirectResponse(
            "/admin/destinations",
            status_code=303
        )

    image_paths = [
        os.path.join(UPLOAD_FOLDER, image.image_path)
        for image in destination.images
    ]

    try:
        db.delete(destination)
        db.commit()

        for file_path in image_paths:
            if os.path.exists(file_path):
                os.remove(file_path)

    except Exception:
        db.rollback()

        return RedirectResponse(
            "/admin/destinations?error=delete_failed",
            status_code=303
        )

    return RedirectResponse(
        "/admin/destinations",
        status_code=303
    )