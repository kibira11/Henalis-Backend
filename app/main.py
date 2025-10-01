# app/main.py
from fastapi import FastAPI

# FastAPI instance MUST be called "app"
app = FastAPI(title="Furniture E-commerce Backend")

@app.get("/")
async def root():
    return {"message": "Backend is running!"}
