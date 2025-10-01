# tests/test_shop.py

"""
Tests for the Shop module.
Uses pytest and httpx.AsyncClient to test the FastAPI endpoints.
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool
from uuid import uuid4
from decimal import Decimal

from app.main import app
from app.database import Base, get_db
from app.dependencies import get_current_user, get_current_admin
from app.models.shop import Category, Material, Tag, Item


# Test database URL (use a separate test database)
TEST_DATABASE_URL = "postgresql+asyncpg://user:password@localhost:5432/furniture_test_db"

# Create test engine
test_engine = create_async_engine(TEST_DATABASE_URL, poolclass=NullPool)
TestSessionLocal = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)


@pytest_asyncio.fixture
async def db_session():
    """Create a fresh database session for each test."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    
    async with TestSessionLocal() as session:
        yield session


@pytest_asyncio.fixture
async def client(db_session):
    """Create a test client with overridden dependencies."""
    
    async def override_get_db():
        yield db_session
    
    # Mock user for authenticated endpoints
    async def mock_current_user():
        return {
            "user_id": "00000000-0000-0000-0000-000000000001",
            "payload": {"sub": "00000000-0000-0000-0000-000000000001", "role": "user"}
        }
    
    # Mock admin for admin endpoints
    async def mock_current_admin():
        return {
            "user_id": "00000000-0000-0000-0000-000000000002",
            "payload": {"sub": "00000000-0000-0000-0000-000000000002", "role": "admin"}
        }
    
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = mock_current_user
    app.dependency_overrides[get_current_admin] = mock_current_admin
    
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
    
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_create_category(client: AsyncClient):
    """Test creating a new category."""
    response = await client.post(
        "/api/categories",
        json={
            "name": "Living Room",
            "slug": "living-room",
            "description": "Furniture for living spaces"
        }
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Living Room"
    assert data["slug"] == "living-room"
    assert "id" in data


@pytest.mark.asyncio
async def test_list_categories(client: AsyncClient, db_session: AsyncSession):
    """Test listing categories."""
    # Create test categories
    categories = [
        Category(id=uuid4(), name="Living Room", slug="living-room"),
        Category(id=uuid4(), name="Bedroom", slug="bedroom"),
    ]
    db_session.add_all(categories)
    await db_session.commit()
    
    response = await client.get("/api/categories")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2


@pytest.mark.asyncio
async def test_create_item(client: AsyncClient, db_session: AsyncSession):
    """Test creating a new item."""
    # Create a category first
    category = Category(id=uuid4(), name="Living Room", slug="living-room")
    db_session.add(category)
    await db_session.commit()
    
    response = await client.post(
        "/api/items",
        json={
            "name": "Modern Sofa",
            "sku": "SOFA-001",
            "description": "A comfortable sofa",
            "price_decimal": "599.99",
            "currency": "USD",
            "category_id": str(category.id),
            "stock_quantity": 10,
            "is_active": True
        }
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Modern Sofa"
    assert data["sku"] == "SOFA-001"
    assert float(data["price_decimal"]) == 599.99


@pytest.mark.asyncio
async def test_list_items_with_filters(client: AsyncClient, db_session: AsyncSession):
    """Test listing items with filters and pagination."""
    # Create test data
    category = Category(id=uuid4(), name="Living Room", slug="living-room")
    db_session.add(category)
    await db_session.flush()
    
    items = [
        Item(
            id=uuid4(),
            name="Sofa 1",
            sku="SOFA-001",
            price_decimal=Decimal("599.99"),
            category_id=category.id,
            stock_quantity=10,
            is_active=True
        ),
        Item(
            id=uuid4(),
            name="Sofa 2",
            sku="SOFA-002",
            price_decimal=Decimal("799.99"),
            category_id=category.id,
            stock_quantity=5,
            is_active=True
        ),
        Item(
            id=uuid4(),
            name="Chair 1",
            sku="CHAIR-001",
            price_decimal=Decimal("199.99"),
            category_id=category.id,
            stock_quantity=20,
            is_active=False
        ),
    ]
    db_session.add_all(items)
    await db_session.commit()
    
    # Test basic listing
    response = await client.get("/api/items")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "meta" in data
    assert data["meta"]["total"] >= 2
    
    # Test filtering by active status
    response = await client.get("/api/items?is_active=true")
    data = response.json()
    assert all(item["is_active"] for item in data["items"])
    
    # Test price filtering
    response = await client.get("/api/items?price_min=500&price_max=800")
    data = response.json()
    for item in data["items"]:
        assert 500 <= float(item["price_decimal"]) <= 800
    
    # Test search
    response = await client.get("/api/items?q=Sofa")
    data = response.json()
    assert all("Sofa" in item["name"] for item in data["items"])


@pytest.mark.asyncio
async def test_item_sorting(client: AsyncClient, db_session: AsyncSession):
    """Test item sorting functionality."""
    category = Category(id=uuid4(), name="Test", slug="test")
    db_session.add(category)
    await db_session.flush()
    
    items = [
        Item(id=uuid4(), name="Item A", sku="A", price_decimal=Decimal("100"), 
             category_id=category.id, likes=10),
        Item(id=uuid4(), name="Item B", sku="B", price_decimal=Decimal("200"), 
             category_id=category.id, likes=50),
        Item(id=uuid4(), name="Item C", sku="C", price_decimal=Decimal("150"), 
             category_id=category.id, likes=30),
    ]
    db_session.add_all(items)
    await db_session.commit()
    
    # Test price-low sorting
    response = await client.get("/api/items?sort=price-low")
    data = response.json()
    prices = [float(item["price_decimal"]) for item in data["items"]]
    assert prices == sorted(prices)
    
    # Test most-loved sorting
    response = await client.get("/api/items?sort=most-loved")
    data = response.json()
    likes = [item["likes"] for item in data["items"]]
    assert likes == sorted(likes, reverse=True)


@pytest.mark.asyncio
async def test_get_item_detail(client: AsyncClient, db_session: AsyncSession):
    """Test getting item detail with relationships."""
    category = Category(id=uuid4(), name="Living Room", slug="living-room")
    material = Material(id=uuid4(), name="Oak Wood")
    tag = Tag(id=uuid4(), name="modern")
    
    db_session.add_all([category, material, tag])
    await db_session.flush()
    
    item = Item(
        id=uuid4(),
        name="Test Item",
        sku="TEST-001",
        price_decimal=Decimal("299.99"),
        category_id=category.id,
        material_id=material.id,
        stock_quantity=10
    )
    item.tags.append(tag)
    db_session.add(item)
    await db_session.commit()
    
    response = await client.get(f"/api/items/{item.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(item.id)
    assert data["category"]["name"] == "Living Room"
    assert data["material"]["name"] == "Oak Wood"
    assert len(data["tags"]) == 1
    assert data["tags"][0]["name"] == "modern"


@pytest.mark.asyncio
async def test_update_item(client: AsyncClient, db_session: AsyncSession):
    """Test updating an item."""
    item = Item(
        id=uuid4(),
        name="Old Name",
        sku="TEST-001",
        price_decimal=Decimal("100"),
        stock_quantity=5
    )
    db_session.add(item)
    await db_session.commit()
    
    response = await client.patch(
        f"/api/items/{item.id}",
        json={"name": "New Name", "price_decimal": "150.00"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "New Name"
    assert float(data["price_decimal"]) == 150.00


@pytest.mark.asyncio
async def test_delete_item(client: AsyncClient, db_session: AsyncSession):
    """Test deleting an item."""
    item = Item(
        id=uuid4(),
        name="To Delete",
        sku="DEL-001",
        price_decimal=Decimal("100"),
        stock_quantity=1
    )
    db_session.add(item)
    await db_session.commit()
    
    response = await client.delete(f"/api/items/{item.id}")
    assert response.status_code == 204
    
    # Verify deletion
    response = await client.get(f"/api/items/{item.id}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_bulk_update_items(client: AsyncClient, db_session: AsyncSession):
    """Test bulk updating items."""
    items = [
        Item(id=uuid4(), name=f"Item {i}", sku=f"SKU-{i}", 
             price_decimal=Decimal("100"), stock_quantity=10, is_active=True)
        for i in range(3)
    ]
    db_session.add_all(items)
    await db_session.commit()
    
    item_ids = [str(item.id) for item in items]
    
    response = await client.patch(
        "/api/items",
        json={
            "ids": item_ids,
            "patch": {"is_active": False}
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["updated"] == 3


@pytest.mark.asyncio
async def test_bulk_delete_items(client: AsyncClient, db_session: AsyncSession):
    """Test bulk deleting items."""
    items = [
        Item(id=uuid4(), name=f"Item {i}", sku=f"SKU-{i}", 
             price_decimal=Decimal("100"), stock_quantity=10)
        for i in range(3)
    ]
    db_session.add_all(items)
    await db_session.commit()
    
    item_ids = [str(item.id) for item in items]
    
    response = await client.delete(
        "/api/items",
        json={"ids": item_ids}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["deleted"] == 3


@pytest.mark.asyncio
async def test_like_item(client: AsyncClient, db_session: AsyncSession):
    """Test liking an item."""
    item = Item(
        id=uuid4(),
        name="Test Item",
        sku="TEST-001",
        price_decimal=Decimal("100"),
        stock_quantity=10,
        likes=5
    )
    db_session.add(item)
    await db_session.commit()
    
    response = await client.post(f"/api/items/{item.id}/like")
    assert response.status_code == 200
    data = response.json()
    assert data["likes"] == 6
    
    # Like again
    response = await client.post(f"/api/items/{item.id}/like")
    data = response.json()
    assert data["likes"] == 7


@pytest.mark.asyncio
async def test_add_to_wishlist(client: AsyncClient, db_session: AsyncSession):
    """Test adding item to wishlist."""
    item = Item(
        id=uuid4(),
        name="Test Item",
        sku="TEST-001",
        price_decimal=Decimal("100"),
        stock_quantity=10
    )
    db_session.add(item)
    await db_session.commit()
    
    response = await client.post(f"/api/wishlist/{item.id}")
    assert response.status_code == 201
    data = response.json()
    assert data["item_id"] == str(item.id)
    
    # Test idempotency - adding again should return existing
    response = await client.post(f"/api/wishlist/{item.id}")
    assert response.status_code == 201


@pytest.mark.asyncio
async def test_get_wishlist(client: AsyncClient, db_session: AsyncSession):
    """Test getting user's wishlist."""
    items = [
        Item(id=uuid4(), name=f"Item {i}", sku=f"SKU-{i}", 
             price_decimal=Decimal("100"), stock_quantity=10)
        for i in range(2)
    ]
    db_session.add_all(items)
    await db_session.commit()
    
    # Add items to wishlist
    for item in items:
        await client.post(f"/api/wishlist/{item.id}")
    
    # Get wishlist
    response = await client.get("/api/wishlist")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2


@pytest.mark.asyncio
async def test_remove_from_wishlist(client: AsyncClient, db_session: AsyncSession):
    """Test removing item from wishlist."""
    item = Item(
        id=uuid4(),
        name="Test Item",
        sku="TEST-001",
        price_decimal=Decimal("100"),
        stock_quantity=10
    )
    db_session.add(item)
    await db_session.commit()
    
    # Add to wishlist
    await client.post(f"/api/wishlist/{item.id}")
    
    # Remove from wishlist
    response = await client.delete(f"/api/wishlist/{item.id}")
    assert response.status_code == 204
    
    # Verify removal
    response = await client.get("/api/wishlist")
    data = response.json()
    assert len(data) == 0


@pytest.mark.asyncio
async def test_clear_wishlist(client: AsyncClient, db_session: AsyncSession):
    """Test clearing entire wishlist."""
    items = [
        Item(id=uuid4(), name=f"Item {i}", sku=f"SKU-{i}", 
             price_decimal=Decimal("100"), stock_quantity=10)
        for i in range(3)
    ]
    db_session.add_all(items)
    await db_session.commit()
    
    # Add items to wishlist
    for item in items:
        await client.post(f"/api/wishlist/{item.id}")
    
    # Clear wishlist
    response = await client.delete("/api/wishlist")
    assert response.status_code == 200
    data = response.json()
    assert data["removed"] == 3
    
    # Verify cleared
    response = await client.get("/api/wishlist")
    data = response.json()
    assert len(data) == 0


@pytest.mark.asyncio
async def test_assign_tags_to_item(client: AsyncClient, db_session: AsyncSession):
    """Test assigning tags to an item."""
    item = Item(id=uuid4(), name="Item", sku="SKU-001", 
                price_decimal=Decimal("100"), stock_quantity=10)
    tags = [Tag(id=uuid4(), name=f"tag{i}") for i in range(3)]
    
    db_session.add_all([item] + tags)
    await db_session.commit()
    
    tag_ids = [str(tag.id) for tag in tags]
    response = await client.post(
        f"/api/items/{item.id}/tags",
        json={"tag_ids": tag_ids}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3


@pytest.mark.asyncio
async def test_remove_tag_from_item(client: AsyncClient, db_session: AsyncSession):
    """Test removing a tag from an item."""
    item = Item(id=uuid4(), name="Item", sku="SKU-001", 
                price_decimal=Decimal("100"), stock_quantity=10)
    tag = Tag(id=uuid4(), name="test-tag")
    item.tags.append(tag)
    
    db_session.add_all([item, tag])
    await db_session.commit()
    
    response = await client.delete(f"/api/items/{item.id}/tags/{tag.id}")
    assert response.status_code == 204