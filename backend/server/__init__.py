from fastapi import FastAPI
from backend.api.route import upload,chat
from backend.core.config import settings
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware import Middleware
from contextlib import asynccontextmanager
from backend.models.surya_ocr import SuryaProcessor
from backend.models.visual_handler import VisionProcessor


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.processor = SuryaProcessor()
   
    yield
    app.state.processor = None
    


def create_app():
    app = FastAPI(
        title=settings.API_TITLE,
        description=settings.API_DESCRIPTION,
        version=settings.API_VERSION,
        docs_url="/",
        lifespan=lifespan,
        middleware=[
            Middleware(
                CORSMiddleware,
                allow_origins=["*"],
                allow_credentials=True,
                allow_methods=["*"],
                allow_headers=["*"],
            ),
        ],
    )

    app.include_router(upload.router, prefix="/api/v1")
    app.include_router(chat.router, prefix="/api/v1")

    return app


app = create_app()
