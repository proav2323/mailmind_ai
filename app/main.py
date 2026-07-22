from fastapi import FastAPI

app = FastAPI()


@app.get("/")
def root():
    return {
        "message": "Hello from FastAPI on Vercel!"
    }


@app.get("/hello/{name}")
def hello(name: str):
    return {
        "message": f"Hello {name}"
    }