from fastapi import APIRouter

router = APIRouter(prefix="/contact", tags=["Contact"])

@router.get("/")
def get_contact():
    return {"message": "Contact endpoint working"}
