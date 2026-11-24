
from datetime import timedelta

from fastapi import APIRouter, Request, Depends, Form, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.database import get_database
from app.models import User, Booking
from app.security import (
    hash_password,
    verify_password,
    create_access_token
)
from app.templating import templates


router = APIRouter(tags=["Authentication"])


@router.get("/register", response_class=HTMLResponse)
def register_page(request: Request):
    return templates.TemplateResponse(
        request,
        "register.html",
        {"title": "Register"}
    )


@router.post("/register", response_class=HTMLResponse)
def register(
    request: Request,
    name: str = Form(...),
    email: str = Form(...),
    phone: str = Form(""),
    password: str = Form(...),
    confirm: str = Form(...),
    db: Session = Depends(get_database),
):
    email = email.strip().lower()
    error = None

    if not name.strip() or not email:
        error = "Name and email are required."

    elif len(password) < 6:
        error = "Password must be at least 6 characters."

    elif len(password.encode("utf-8")) > 72:
        error = "Password is too long."

    elif password != confirm:
        error = "Passwords do not match."

    elif db.scalar(select(User).where(User.email == email)):
        error = "An account with this email already exists."

    if error:
        return templates.TemplateResponse(
            request,
            "register.html",
            {
                "title": "Register",
                "error": error,
                "name": name,
                "email": email,
                "phone": phone,
            },
            status_code=400,
        )

    user = User(
        name=name.strip(),
        email=email,
        phone=phone.strip(),
        password_hash=hash_password(password),
        role="customer",
    )

    db.add(user)
    db.commit()

    return RedirectResponse(
        "/login?registered=1",
        status_code=303
    )


@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse(
        request,
        "login.html",
        {"title": "Login"}
    )


@router.post("/login", response_class=HTMLResponse)
def login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_database),
):
    email = email.strip().lower()

    user = db.scalar(
        select(User).where(User.email == email)
    )

    if not user or not verify_password(password, user.password_hash):
        return templates.TemplateResponse(
            request,
            "login.html",
            {
                "title": "Login",
                "error": "Invalid email or password.",
                "email": email,
            },
            status_code=401,
        )

    request.session["user"] = {
        "id": user.id,
        "name": user.name,
        "role": user.role,
    }

    if user.role == "admin":
        return RedirectResponse(
            "/admin/dashboard",
            status_code=303
        )

    return RedirectResponse(
        "/user/dashboard",
        status_code=303
    )


@router.post("/token")
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_database)
):
    email = form_data.username.strip().lower()

    user = db.scalar(
        select(User).where(User.email == email)
    )

    if not user or not verify_password(
        form_data.password,
        user.password_hash
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"}
        )

    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required."
        )

    access_token = create_access_token(
        data={
            "sub": str(user.id),
            "email": user.email,
            "role": user.role
        }
    )

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }


@router.get("/user/dashboard", response_class=HTMLResponse)
def user_dashboard(
    request: Request,
    db: Session = Depends(get_database),
):
    current_user = request.session.get("user")

    if not current_user:
        return RedirectResponse(
            "/login",
            status_code=303
        )

    if current_user.get("role") != "customer":
        return RedirectResponse(
            "/",
            status_code=303
        )

    bookings = db.scalars(
        select(Booking)
        .options(selectinload(Booking.houseboat))
        .where(Booking.user_id == current_user["id"])
        .order_by(Booking.created_at.desc())
    ).all()

    return templates.TemplateResponse(
        request,
        "user_dashboard.html",
        {
            "title": "My Dashboard",
            "user": current_user,
            "bookings": bookings,
            "timedelta": timedelta,
        }
    )


@router.get("/logout")
def logout(request: Request):
    request.session.clear()

    return RedirectResponse(
        "/login",
        status_code=303
    )
