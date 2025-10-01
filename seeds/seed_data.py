# seeds/seed_data.py

"""
Seed data script for populating the database with sample data.
Run with: python -m seeds.seed_data
"""

import asyncio
import sys
from pathlib import Path
import uuid
from decimal import Decimal

# Add parent directory to path so "app" package is importable
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.database import AsyncSessionLocal
from app.models.shop import Category, Material, Tag, Item, Wishlist


async def seed_data():
    """Populate database with sample data."""
    async with AsyncSessionLocal() as db:
        print("Starting database seeding...")

        # Wipe tables first (idempotent seeding)
        await db.execute(text("TRUNCATE wishlist, item_tags, items, tags, materials, categories CASCADE"))
        await db.commit()
        print("✓ Cleared existing data")

        # ========================
        # Categories
        # ========================
        categories = [
            Category(
                id=uuid.uuid4(),
                name="Living Room",
                slug="living-room",
                description="Furniture for your living space"
            ),
            Category(
                id=uuid.uuid4(),
                name="Bedroom",
                slug="bedroom",
                description="Comfortable bedroom furniture"
            ),
            Category(
                id=uuid.uuid4(),
                name="Dining Room",
                slug="dining-room",
                description="Dining tables and chairs"
            ),
        ]
        db.add_all(categories)
        await db.flush()
        print(f"✓ Created {len(categories)} categories")

        # ========================
        # Materials
        # ========================
        materials = [
            Material(id=uuid.uuid4(), name="Oak Wood", description="Solid oak wood, durable and beautiful"),
            Material(id=uuid.uuid4(), name="Fabric", description="High-quality upholstery fabric"),
            Material(id=uuid.uuid4(), name="Leather", description="Genuine leather"),
            Material(id=uuid.uuid4(), name="Metal", description="Powder-coated metal frame"),
        ]
        db.add_all(materials)
        await db.flush()
        print(f"✓ Created {len(materials)} materials")

        # ========================
        # Tags
        # ========================
        tags = [
            Tag(id=uuid.uuid4(), name="modern"),
            Tag(id=uuid.uuid4(), name="vintage"),
            Tag(id=uuid.uuid4(), name="minimalist"),
            Tag(id=uuid.uuid4(), name="luxury"),
            Tag(id=uuid.uuid4(), name="eco-friendly"),
        ]
        db.add_all(tags)
        await db.flush()
        print(f"✓ Created {len(tags)} tags")

        # ========================
        # Items
        # ========================
        items = [
            Item(
                id=uuid.uuid4(),
                name="Modern Sofa",
                sku="SOFA-001",
                description="A comfortable 3-seater sofa with modern design",
                price_decimal=Decimal("599.99"),
                currency="USD",
                category_id=categories[0].id,
                material_id=materials[1].id,
                stock_quantity=15,
                likes=42,
                is_active=True
            ),
            Item(
                id=uuid.uuid4(),
                name="Oak Dining Table",
                sku="TABLE-001",
                description="Solid oak dining table, seats 6",
                price_decimal=Decimal("899.99"),
                currency="USD",
                category_id=categories[2].id,
                material_id=materials[0].id,
                stock_quantity=8,
                likes=28,
                is_active=True
            ),
            Item(
                id=uuid.uuid4(),
                name="Leather Armchair",
                sku="CHAIR-001",
                description="Luxurious leather armchair",
                price_decimal=Decimal("449.99"),
                currency="USD",
                category_id=categories[0].id,
                material_id=materials[2].id,
                stock_quantity=12,
                likes=35,
                is_active=True
            ),
            Item(
                id=uuid.uuid4(),
                name="King Size Bed Frame",
                sku="BED-001",
                description="Elegant king size bed frame with headboard",
                price_decimal=Decimal("799.99"),
                currency="USD",
                category_id=categories[1].id,
                material_id=materials[0].id,
                stock_quantity=5,
                likes=56,
                is_active=True
            ),
            Item(
                id=uuid.uuid4(),
                name="Coffee Table",
                sku="TABLE-002",
                description="Modern coffee table with glass top",
                price_decimal=Decimal("199.99"),
                currency="USD",
                category_id=categories[0].id,
                material_id=materials[3].id,
                stock_quantity=20,
                likes=18,
                is_active=True
            ),
            Item(
                id=uuid.uuid4(),
                name="Nightstand Set",
                sku="NIGHT-001",
                description="Set of 2 matching nightstands",
                price_decimal=Decimal("149.99"),
                currency="USD",
                category_id=categories[1].id,
                material_id=materials[0].id,
                stock_quantity=10,
                likes=12,
                is_active=True
            ),
            Item(
                id=uuid.uuid4(),
                name="Dining Chairs (Set of 4)",
                sku="CHAIR-002",
                description="Comfortable dining chairs, set of 4",
                price_decimal=Decimal("299.99"),
                currency="USD",
                category_id=categories[2].id,
                material_id=materials[1].id,
                stock_quantity=15,
                likes=22,
                is_active=True
            ),
            Item(
                id=uuid.uuid4(),
                name="Bookshelf",
                sku="SHELF-001",
                description="5-tier bookshelf, perfect for any room",
                price_decimal=Decimal("179.99"),
                currency="USD",
                category_id=categories[0].id,  # ✅ fixed bug
                material_id=materials[0].id,
                stock_quantity=18,
                likes=15,
                is_active=True
            ),
            Item(
                id=uuid.uuid4(),
                name="TV Stand",
                sku="STAND-001",
                description="Modern TV stand with storage compartments",
                price_decimal=Decimal("249.99"),
                currency="USD",
                category_id=categories[0].id,
                material_id=materials[0].id,
                stock_quantity=12,
                likes=31,
                is_active=True
            ),
            Item(
                id=uuid.uuid4(),
                name="Wardrobe",
                sku="WARD-001",
                description="Spacious wardrobe with sliding doors",
                price_decimal=Decimal("699.99"),
                currency="USD",
                category_id=categories[1].id,
                material_id=materials[0].id,
                stock_quantity=6,
                likes=44,
                is_active=True
            ),
        ]

        # Assign tags to items
        items[0].tags = [tags[0], tags[2]]
        items[1].tags = [tags[1], tags[4]]
        items[2].tags = [tags[3]]
        items[3].tags = [tags[0], tags[3]]
        items[4].tags = [tags[0], tags[2]]
        items[5].tags = [tags[2]]
        items[6].tags = [tags[0]]
        items[7].tags = [tags[2], tags[4]]
        items[8].tags = [tags[0]]
        items[9].tags = [tags[0], tags[2]]

        db.add_all(items)
        await db.flush()
        print(f"✓ Created {len(items)} items with tags")

        # ========================
        # Wishlist (sample user)
        # ========================
        sample_user_id = uuid.UUID("00000000-0000-0000-0000-000000000001")
        wishlist_items = [
            Wishlist(id=uuid.uuid4(), user_id=sample_user_id, item_id=items[0].id),
            Wishlist(id=uuid.uuid4(), user_id=sample_user_id, item_id=items[3].id),
        ]
        db.add_all(wishlist_items)
        await db.flush()
        print(f"✓ Created {len(wishlist_items)} wishlist entries")

        # Commit all
        await db.commit()
        print("\n✅ Database seeding completed successfully!")


if __name__ == "__main__":
    asyncio.run(seed_data())
