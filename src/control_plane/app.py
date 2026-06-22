from fastapi import FastAPI
from mangum import Mangum

from routers.swings import router as swings_router

app = FastAPI(title="FixMySwing control plane")
app.include_router(swings_router)

handler = Mangum(app)