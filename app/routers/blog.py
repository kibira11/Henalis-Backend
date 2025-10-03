from fastapi import (
    APIRouter,
    Depends,
    UploadFile,
    File,
    Query,
    HTTPException,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List, Optional
from uuid import UUID

from app.database import get_db
from app.dependencies import get_current_admin
from app.models import blog as models
from app.schemas import blog as schemas
from app.services import blog_service
from app.storage import storage  # use storage.upload_file()

router = APIRouter(prefix="/api/blog", tags=["Blog"])

# ---------- POSTS ----------

@router.get("/posts", response_model=List[schemas.BlogPostResponse])
async def list_posts(
    db: AsyncSession = Depends(get_db),
    search: Optional[str] = None,
    tag_id: Optional[UUID] = None,
    limit: int = Query(10, ge=1, le=50),
    offset: int = 0,
):
    """List published posts with optional search, filter, pagination"""
    query = select(models.BlogPost).where(models.BlogPost.is_published == True)

    if search:
        query = query.where(models.BlogPost.title.ilike(f"%{search}%"))
    if tag_id:
        query = query.join(models.BlogPost.tags).where(models.BlogTag.id == tag_id)

    query = query.order_by(models.BlogPost.created_at.desc()).limit(limit).offset(offset)
    result = await db.execute(query)
    return result.scalars().unique().all()


@router.get("/posts/{post_id}", response_model=schemas.BlogPostResponse)
async def get_post(post_id: UUID, db: AsyncSession = Depends(get_db)):
    """Fetch a single post by ID"""
    post = await db.get(models.BlogPost, post_id)
    if not post or not post.is_published:
        raise HTTPException(status_code=404, detail="Post not found")
    return post


@router.post(
    "/posts",
    response_model=schemas.BlogPostResponse,
    dependencies=[Depends(get_current_admin)],
)
async def create_post(data: schemas.BlogPostCreate, db: AsyncSession = Depends(get_db)):
    """Admin: Create a new blog post"""
    await blog_service.ensure_unique_slug(db, data.slug)
    tags = await blog_service.get_valid_tags(db, data.tag_ids)

    post = models.BlogPost(
        title=data.title,
        slug=data.slug,
        excerpt=data.excerpt or data.content[:200],  # fallback if excerpt missing
        content=data.content,
        cover_image_url=data.cover_image_url,
        author=data.author,
        is_published=data.is_published,
        read_time=blog_service.calculate_read_time(data.content),
        tags=tags,
    )
    db.add(post)
    await db.commit()
    await db.refresh(post)
    return post


@router.patch(
    "/posts/{post_id}",
    response_model=schemas.BlogPostResponse,
    dependencies=[Depends(get_current_admin)],
)
async def update_post(
    post_id: UUID, data: schemas.BlogPostUpdate, db: AsyncSession = Depends(get_db)
):
    """Admin: Update a blog post"""
    post = await db.get(models.BlogPost, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    if data.slug:
        await blog_service.ensure_unique_slug(db, data.slug, post_id)

    for field, value in data.dict(exclude_unset=True).items():
        if field == "tag_ids":
            post.tags = await blog_service.get_valid_tags(db, value)
        else:
            setattr(post, field, value)

    post.read_time = blog_service.calculate_read_time(post.content)
    await db.commit()
    await db.refresh(post)
    return post


@router.delete("/posts/{post_id}", dependencies=[Depends(get_current_admin)])
async def delete_post(post_id: UUID, db: AsyncSession = Depends(get_db)):
    """Admin: Delete a blog post"""
    post = await db.get(models.BlogPost, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    await db.delete(post)
    await db.commit()
    return {"message": "Post deleted"}


# ---------- TAGS ----------

@router.get("/tags", response_model=List[schemas.BlogTagResponse])
async def list_tags(db: AsyncSession = Depends(get_db)):
    """List all tags"""
    result = await db.execute(select(models.BlogTag))
    return result.scalars().all()


@router.post(
    "/tags",
    response_model=schemas.BlogTagResponse,
    dependencies=[Depends(get_current_admin)],
)
async def create_tag(data: schemas.BlogTagCreate, db: AsyncSession = Depends(get_db)):
    """Admin: Create a tag"""
    tag = models.BlogTag(**data.dict())
    db.add(tag)
    await db.commit()
    await db.refresh(tag)
    return tag


@router.patch(
    "/tags/{tag_id}",
    response_model=schemas.BlogTagResponse,
    dependencies=[Depends(get_current_admin)],
)
async def update_tag(
    tag_id: UUID, data: schemas.BlogTagUpdate, db: AsyncSession = Depends(get_db)
):
    """Admin: Update a tag"""
    tag = await db.get(models.BlogTag, tag_id)
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    for field, value in data.dict(exclude_unset=True).items():
        setattr(tag, field, value)
    await db.commit()
    await db.refresh(tag)
    return tag


@router.delete("/tags/{tag_id}", dependencies=[Depends(get_current_admin)])
async def delete_tag(tag_id: UUID, db: AsyncSession = Depends(get_db)):
    """Admin: Delete a tag"""
    tag = await db.get(models.BlogTag, tag_id)
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    await db.delete(tag)
    await db.commit()
    return {"message": "Tag deleted"}


# ---------- IMAGE UPLOAD ----------

@router.post("/upload-image")
async def upload_image(
    file: UploadFile = File(...), admin=Depends(get_current_admin)
):
    """Admin: Upload blog cover image"""
    _, public_url = await storage.upload_file(file, folder="blog")
    return {"url": public_url}
