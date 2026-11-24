
from app.database import SessionLocal
from app.models import Houseboat

db = SessionLocal()

try:
    existing = db.query(Houseboat).count()

    if existing > 0:
        print("Houseboats already exist!")
    else:
        houseboats = [
            Houseboat(
                name="Luxury Kerala Houseboat",
                location="Alappuzha",
                description="Enjoy a relaxing journey through the beautiful Kerala backwaters.",
                facilities="AC, WiFi, Dining, Bedroom",
                bedrooms=2,
                capacity=4,
                price_per_night=12000,
                is_active=True
            ),

            Houseboat(
                name="Premium Backwater Houseboat",
                location="Kumarakom",
                description="Experience a peaceful stay surrounded by nature.",
                facilities="AC, WiFi, Kitchen, Dining",
                bedrooms=3,
                capacity=6,
                price_per_night=15000,
                is_active=True
            ),

            Houseboat(
                name="Deluxe Family Houseboat",
                location="Kochi",
                description="A comfortable houseboat experience for families.",
                facilities="AC, TV, Dining, Bedroom",
                bedrooms=2,
                capacity=5,
                price_per_night=10000,
                is_active=True
            )
        ]

        db.add_all(houseboats)
        db.commit()

        print("3 sample houseboats added successfully!")

except Exception as e:
    db.rollback()
    print("Error:", e)

finally:
    db.close()
