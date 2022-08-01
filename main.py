from fastapi import FastAPI

from routers import auth, feed

app = FastAPI()

# Routers
app.include_router(auth.router, tags=["auth"])
app.include_router(feed.router, tags=["feed"])


@app.get("/healthcheck")
def health_check():
    return {"msg": "OK"}
