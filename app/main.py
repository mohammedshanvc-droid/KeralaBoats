import os
from dotenv import load_dotenv

from fastapi import FastAPI, Request, Depends
from fastapi.staticfiles import StaticFiles
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload
from starlette.middleware.sessions import SessionMiddleware

from app.routers import auth, houseboats, admin, api
from app.database import Base, engine, get_database
from app import models
from app.templating import templates
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

load_dotenv()

app = FastAPI(title="Houseboat Booking System")

app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("SECRET_KEY")
)

app.mount(
    "/static",
    StaticFiles(directory="app/static"),
    name="static"
)

Base.metadata.create_all(bind=engine)

app.include_router(auth.router)
app.include_router(houseboats.router)
app.include_router(admin.router)
app.include_router(api.router)


@app.get("/")
def home(request: Request, db: Session = Depends(get_database)):
    featured = db.scalars(
        select(models.Houseboat)
        .options(selectinload(models.Houseboat.images))
        .where(models.Houseboat.is_active.is_(True))
        .order_by(models.Houseboat.id.desc())
        .limit(3)
    ).all()

    return templates.TemplateResponse(
        request,
        "home.html",
        {
            "title": "Home",
            "user": request.session.get("user"),
            "featured": featured
        }
    )