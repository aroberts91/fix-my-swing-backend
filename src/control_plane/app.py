from fastapi import FastAPI
from mangum import Mangum
from starlette.middleware.cors import CORSMiddleware

from routers.swings import router as swings_router

app = FastAPI(title="FixMySwing control plane")
app.include_router(swings_router)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"]
)

handler = Mangum(app)