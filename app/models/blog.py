import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, Text, DateTime, ForeignKey, Table, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base

# Association table for many-to-many between BlogPost and BlogTag
post_tag_association = Table(
    "post_tag_association",
    Base.metadata,
    Column("post_id", UUID(as_uuid=True), ForeignKey("blog_posts.id", ondelete="CASCADE")),
    Column("tag_id", UUID(as_uuid=True), ForeignKey("blog_tags.id", ondelete="CASCADE")),
)

class BlogPost(Base):
    __tablename__ = "blog_posts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(255), nullable=False)
    slug = Column(String(255), unique=True, index=True, nullable=False)
    excerpt = Column(String(500), nullable=True)  # short preview text
    content = Column(Text, nullable=False)
    cover_image_url = Column(String(500), nullable=True)
    author = Column(String(255), nullable=False)  # frontend requires string author
    read_time = Column(String(50), nullable=True)  # e.g., "5 min read"
    is_published = Column(Boolean, default=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    tags = relationship("BlogTag", secondary=post_tag_association, back_populates="posts")


class BlogTag(Base):
    __tablename__ = "blog_tags"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), unique=True, nullable=False)
    is_category = Column(Boolean, default=False)  # distinguish category vs tag

    posts = relationship("BlogPost", secondary=post_tag_association, back_populates="tags")
