import math
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import HTTPException
from app.models.blog import BlogPost, BlogTag

# Utility: Calculate reading time based on word count
def calculate_read_time(content: str) -> str:
    words = len(content.split())
    minutes = max(1, math.ceil(words / 200))  # assume ~200 WPM
    return f"{minutes} min read"

# Utility: Ensure slug uniqueness
async def ensure_unique_slug(db: AsyncSession, slug: str, post_id=None):
    result = await db.execute(select(BlogPost).where(BlogPost.slug == slug))
    existing = result.scalar_one_or_none()
    if existing and existing.id != post_id:
        raise HTTPException(status_code=400, detail="Slug already exists")

# Utility: Validate tag ids exist
async def get_valid_tags(db: AsyncSession, tag_ids):
    if not tag_ids:
        return []
    result = await db.execute(select(BlogTag).where(BlogTag.id.in_(tag_ids)))
    tags = result.scalars().all()
    if len(tags) != len(tag_ids):
        raise HTTPException(status_code=400, detail="One or more tags not found")
    return tags
