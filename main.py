from fastapi import FastAPI

app = FastAPI()

@app.get("/healthcheck")
def health_check():
    return {"msg": "OK"}

