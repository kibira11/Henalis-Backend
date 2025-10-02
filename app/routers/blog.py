from fastapi import APIRouter

router = APIRouter(prefix="/blog", tags=["Blog"])

@router.get("/")
def get_blog():
    return {"message": "Blog endpoint working"}
