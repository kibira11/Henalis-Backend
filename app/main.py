# app/main.py
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.routers import shop, contact, blog, subscriber  # ✅ include subscriber

app = FastAPI(
    title="Furniture E-commerce Backend",
    version="0.1.0",
    description="Backend API for the Henalis Furniture E-commerce system"
)

# ✅ Serve static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Root route
@app.get("/")
def root():
    return {"message": "Welcome to the Furniture E-commerce Backend API"}

# Register routers
app.include_router(shop.router)
app.include_router(contact.router)
app.include_router(blog.router)
app.include_router(subscriber.router)  # ✅ added
