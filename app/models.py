
from datetime import datetime, date
from typing import Optional

from sqlalchemy import (
    String,
    Text,
    Integer,
    Numeric,
    Date,
    DateTime,
    Boolean,
    ForeignKey
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(150), unique=True, index=True)
    phone: Mapped[Optional[str]] = mapped_column(String(20))
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(20), default="customer")
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )

    bookings: Mapped[list["Booking"]] = relationship(back_populates="user")
    reviews: Mapped[list["Review"]] = relationship(back_populates="user")


class Houseboat(Base):
    __tablename__ = "houseboats"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(150))
    location: Mapped[str] = mapped_column(String(100), index=True)
    description: Mapped[Optional[str]] = mapped_column(Text)
    facilities: Mapped[Optional[str]] = mapped_column(Text)

    bedrooms: Mapped[int] = mapped_column(Integer, default=1)
    capacity: Mapped[int] = mapped_column(Integer, default=2)
    price_per_night: Mapped[float] = mapped_column(Numeric(10, 2))

    food_available: Mapped[Optional[str]] = mapped_column(
        String(30),
        nullable=True
    )

    meal_options: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True
    )

    food_menu: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )

    special_food: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True
    )

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )

    images: Mapped[list["HouseboatImage"]] = relationship(
        back_populates="houseboat",
        cascade="all, delete-orphan"
    )

    bookings: Mapped[list["Booking"]] = relationship(
        back_populates="houseboat",
        cascade="all, delete-orphan"
    )

    reviews: Mapped[list["Review"]] = relationship(
        back_populates="houseboat",
        cascade="all, delete-orphan"
    )


class HouseboatImage(Base):
    __tablename__ = "houseboat_images"

    id: Mapped[int] = mapped_column(primary_key=True)
    houseboat_id: Mapped[int] = mapped_column(
        ForeignKey("houseboats.id")
    )
    image_path: Mapped[str] = mapped_column(String(255))
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False)

    houseboat: Mapped["Houseboat"] = relationship(
        back_populates="images"
    )


class Booking(Base):
    __tablename__ = "bookings"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    houseboat_id: Mapped[int] = mapped_column(
        ForeignKey("houseboats.id")
    )
    check_in: Mapped[date] = mapped_column(Date)
    nights: Mapped[int] = mapped_column(Integer)
    guests: Mapped[int] = mapped_column(Integer)
    total_amount: Mapped[float] = mapped_column(Numeric(10, 2))
    status: Mapped[str] = mapped_column(String(20), default="pending")
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )

    user: Mapped["User"] = relationship(back_populates="bookings")
    houseboat: Mapped["Houseboat"] = relationship(
        back_populates="bookings"
    )


class Review(Base):
    __tablename__ = "reviews"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    houseboat_id: Mapped[int] = mapped_column(
        ForeignKey("houseboats.id")
    )
    rating: Mapped[int] = mapped_column(Integer)
    comment: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )

    user: Mapped["User"] = relationship(back_populates="reviews")
    houseboat: Mapped["Houseboat"] = relationship(
        back_populates="reviews"
    )


class Destination(Base):
    __tablename__ = "destinations"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(150))
    location: Mapped[str] = mapped_column(String(150))
    description: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )

    images: Mapped[list["DestinationImage"]] = relationship(
        back_populates="destination",
        cascade="all, delete-orphan"
    )


class DestinationImage(Base):
    __tablename__ = "destination_images"

    id: Mapped[int] = mapped_column(primary_key=True)
    destination_id: Mapped[int] = mapped_column(
        ForeignKey("destinations.id")
    )
    image_path: Mapped[str] = mapped_column(String(255))

    destination: Mapped["Destination"] = relationship(
        back_populates="images"
    )
