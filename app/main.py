from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse, RedirectResponse
from app.api.routes import router as files_router
from app.models.schemas import ErrorResponse

app = FastAPI(
    title="Geospatial File Measurement API",
    description="A clean backend service built with FastAPI, GeoPandas, PyProj, and Shapely to process geospatial files (.kml and Shapefile .zip) and calculate accurate spatial measurements.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Register API routes
app.include_router(files_router)


@app.get("/", include_in_schema=False)
async def root():
    """Redirect root path to interactive Swagger documentation."""
    return RedirectResponse(url="/docs")


@app.exception_handler(Exception)
async def custom_global_exception_handler(request: Request, exc: Exception):
    """
    Global exception handler to ensure internal server errors return structured JSON
    without leaking Python stack traces to API consumers.
    """
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal server error occurred while processing your request.", "error_code": "INTERNAL_SERVER_ERROR"}
    )
