# app/services/subscriber_service.py
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.subscriber import Subscriber
from app.schemas.subscriber import SubscriberCreate

def create_subscriber(db: Session, subscriber: SubscriberCreate):
    # check if already subscribed
    existing = db.query(Subscriber).filter(Subscriber.email == subscriber.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already subscribed"
        )

    new_subscriber = Subscriber(email=subscriber.email)
    db.add(new_subscriber)
    db.commit()
    db.refresh(new_subscriber)
    return new_subscriber

def list_subscribers(db: Session):
    return db.query(Subscriber).all()
