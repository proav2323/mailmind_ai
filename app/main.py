from app.groq_api import getSummaryOfEmail
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def root():
    return getSummaryOfEmail()