import os

from fastapi import APIRouter, Request, Depends, HTTPException, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.database import get_database
from app.models import Houseboat, Destination, Review
from app.templating import templates

router = APIRouter()


@router.get("/houseboats", response_class=HTMLResponse)
def houseboat_list(
    request: Request,
    location: str = "",
    db: Session = Depends(get_database),
):
    if not request.session.get("user"):
        return RedirectResponse(url="/login", status_code=303)

    location = location.strip()

    query = (
        select(Houseboat)
        .options(selectinload(Houseboat.images))
        .where(Houseboat.is_active.is_(True))
    )

    if location:
        query = query.where(Houseboat.location.like(f"%{location}%"))

    houseboats = db.scalars(
        query.order_by(Houseboat.id.desc())
    ).all()

    locations = db.scalars(
        select(Houseboat.location)
        .where(Houseboat.is_active.is_(True))
        .distinct()
        .order_by(Houseboat.location)
    ).all()

    return templates.TemplateResponse(
        request=request,
        name="houseboats.html",
        context={
            "title": "Houseboats",
            "houseboats": houseboats,
            "locations": locations,
            "search": location,
        },
    )


@router.get("/houseboats/{houseboat_id}", response_class=HTMLResponse)
def houseboat_detail(
    request: Request,
    houseboat_id: int,
    db: Session = Depends(get_database),
):
    if not request.session.get("user"):
        return RedirectResponse(url="/login", status_code=303)

    houseboat = db.scalar(
        select(Houseboat)
        .options(selectinload(Houseboat.images))
        .where(Houseboat.id == houseboat_id)
    )

    if not houseboat or not houseboat.is_active:
        raise HTTPException(
            status_code=404,
            detail="Houseboat not found"
        )

    facilities = [
        f.strip()
        for f in (houseboat.facilities or "").split(",")
        if f.strip()
    ]

    reviews = db.scalars(
        select(Review)
        .options(selectinload(Review.user))
        .where(Review.houseboat_id == houseboat_id)
        .order_by(Review.created_at.desc())
    ).all()

    return templates.TemplateResponse(
        request=request,
        name="houseboat_detail.html",
        context={
            "title": houseboat.name,
            "hb": houseboat,
            "facilities": facilities,
            "reviews": reviews,
            "review_status": request.query_params.get("review"),
            "whatsapp": os.getenv("ADMIN_WHATSAPP", "917510847452"),
        },
    )


@router.post("/houseboats/{houseboat_id}/reviews")
def submit_review(
    request: Request,
    houseboat_id: int,
    rating: int = Form(...),
    comment: str = Form(""),
    db: Session = Depends(get_database),
):
    user = request.session.get("user")

    if not user:
        return RedirectResponse(url="/login", status_code=303)

    if user.get("role") != "customer":
        return RedirectResponse(
            url=f"/houseboats/{houseboat_id}",
            status_code=303
        )

    houseboat = db.get(Houseboat, houseboat_id)

    if not houseboat or not houseboat.is_active:
        raise HTTPException(
            status_code=404,
            detail="Houseboat not found"
        )

    if rating < 1 or rating > 5 or len(comment) > 2000:
        return RedirectResponse(
            url=f"/houseboats/{houseboat_id}?review=invalid#reviews",
            status_code=303
        )

    existing_review = db.scalar(
        select(Review).where(
            Review.user_id == user["id"],
            Review.houseboat_id == houseboat_id
        )
    )

    if existing_review:
        return RedirectResponse(
            url=f"/houseboats/{houseboat_id}?review=already_submitted#reviews",
            status_code=303
        )

    new_review = Review(
        user_id=user["id"],
        houseboat_id=houseboat_id,
        rating=rating,
        comment=comment.strip() or None,
    )

    db.add(new_review)
    db.commit()

    return RedirectResponse(
        url=f"/houseboats/{houseboat_id}?review=success#reviews",
        status_code=303
    )


@router.post("/houseboats/{houseboat_id}/reviews/{review_id}/edit")
def edit_review(
    request: Request,
    houseboat_id: int,
    review_id: int,
    rating: int = Form(...),
    comment: str = Form(""),
    db: Session = Depends(get_database),
):
    user = request.session.get("user")

    if not user:
        return RedirectResponse(url="/login", status_code=303)

    if user.get("role") != "customer":
        return RedirectResponse(
            url=f"/houseboats/{houseboat_id}#reviews",
            status_code=303
        )

    review = db.scalar(
        select(Review).where(
            Review.id == review_id,
            Review.houseboat_id == houseboat_id
        )
    )

    if not review:
        raise HTTPException(
            status_code=404,
            detail="Review not found"
        )

    if review.user_id != user["id"]:
        raise HTTPException(
            status_code=403,
            detail="You cannot edit another customer's review"
        )

    if rating < 1 or rating > 5 or len(comment) > 2000:
        return RedirectResponse(
            url=f"/houseboats/{houseboat_id}?review=invalid#reviews",
            status_code=303
        )

    review.rating = rating
    review.comment = comment.strip() or None

    db.commit()

    return RedirectResponse(
        url=f"/houseboats/{houseboat_id}?review=updated#reviews",
        status_code=303
    )


@router.get("/destinations", response_class=HTMLResponse)
def explore_destinations(
    request: Request,
    db: Session = Depends(get_database),
):
    if not request.session.get("user"):
        return RedirectResponse(url="/login", status_code=303)

    destinations = db.scalars(
        select(Destination)
        .options(selectinload(Destination.images))
        .order_by(Destination.id.desc())
    ).all()

    return templates.TemplateResponse(
        request=request,
        name="destinations.html",
        context={
            "title": "Explore Destinations",
            "destinations": destinations,
        },
    )