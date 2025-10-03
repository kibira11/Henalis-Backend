from typing import List, Optional
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel

# ---------- TAG SCHEMAS ----------
class BlogTagBase(BaseModel):
    name: str
    is_category: bool = False

class BlogTagCreate(BlogTagBase):
    pass

class BlogTagUpdate(BaseModel):
    name: Optional[str]
    is_category: Optional[bool]

class BlogTagResponse(BlogTagBase):
    id: UUID

    class Config:
        orm_mode = True

# ---------- POST SCHEMAS ----------
class BlogPostBase(BaseModel):
    title: str
    slug: str
    excerpt: Optional[str]
    content: str
    cover_image_url: Optional[str]
    author: str
    is_published: bool = False

class BlogPostCreate(BlogPostBase):
    tag_ids: List[UUID] = []

class BlogPostUpdate(BaseModel):
    title: Optional[str]
    slug: Optional[str]
    excerpt: Optional[str]
    content: Optional[str]
    cover_image_url: Optional[str]
    author: Optional[str]
    is_published: Optional[bool]
    tag_ids: Optional[List[UUID]]

class BlogPostResponse(BlogPostBase):
    id: UUID
    read_time: Optional[str]
    created_at: datetime
    updated_at: datetime
    tags: List[BlogTagResponse] = []

    class Config:
        orm_mode = True
