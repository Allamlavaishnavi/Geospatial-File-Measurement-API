import datetime
import os
from fastapi import APIRouter, UploadFile, File, HTTPException, status
from app.models.schemas import FileSummaryResponse, FileMeasurementsResponse, FileStatusEnum
from app.services.file_service import FileService
from app.services.geospatial_service import GeospatialService
from app.services.measurement_service import MeasurementService
from app.utils.validation import (
    validate_file_extension,
    validate_file_size,
    ValidationError,
    InvalidFileFormatError,
    CorruptedFileError,
    MissingShapefileComponentError
)

router = APIRouter(prefix="/api/files", tags=["Geospatial Files"])

# Singleton instance of file service
file_service = FileService()


@router.post(
    "/",
    response_model=FileSummaryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload and process a geospatial file",
    description="Upload a .kml or .zip Shapefile to extract features, CRS metadata, and geometric measurements."
)
async def upload_file(file: UploadFile = File(...)) -> FileSummaryResponse:
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename missing in uploaded file."
        )

    # 1. Validate file extension
    try:
        file_ext = validate_file_extension(file.filename)
    except InvalidFileFormatError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)

    # 2. Read file content & validate size
    content = await file.read()
    try:
        validate_file_size(content)
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)

    file_id = file_service.generate_id()
    created_at_str = datetime.datetime.now(datetime.timezone.utc).isoformat()

    try:
        # 3. Save uploaded content safely
        saved_file_path = file_service.save_file_content(file_id, file.filename, content)

        # 4. Load geospatial data into GeoDataFrame
        gdf = GeospatialService.load_geospatial_data(saved_file_path, file_ext)

        # 5. Extract CRS & feature count
        crs_str = GeospatialService.extract_crs_name(gdf)
        feature_count = len(gdf)

        # 6. Process geometry measurements
        measurements = MeasurementService.process_gdf_measurements(gdf)

        # Build responses
        summary = FileSummaryResponse(
            id=file_id,
            filename=file.filename,
            feature_count=feature_count,
            crs=crs_str,
            status=FileStatusEnum.COMPLETED,
            created_at=created_at_str
        )

        measurements_response = FileMeasurementsResponse(
            file_id=file_id,
            filename=file.filename,
            feature_count=feature_count,
            measurements=measurements
        )

        # 7. Store records in memory
        file_service.store_file_record(file_id, summary, measurements_response)

        return summary

    except (CorruptedFileError, MissingShapefileComponentError) as ve:
        # Store failed status record if desired or raise 400 clean error
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve)
        )
    except Exception as exc:
        # Clean catch of unexpected internal errors without leaking stack trace
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process geospatial file: {str(exc)}"
        )


@router.get(
    "/{file_id}/",
    response_model=FileSummaryResponse,
    summary="Get file information and summary",
    description="Retrieve processing status, feature count, and CRS metadata for a given file ID."
)
async def get_file_summary(file_id: str) -> FileSummaryResponse:
    summary = file_service.get_summary(file_id)
    if not summary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File record with ID '{file_id}' not found."
        )
    return summary


@router.get(
    "/{file_id}/measurements/",
    response_model=FileMeasurementsResponse,
    summary="Get feature-level measurements",
    description="Retrieve geometric measurements (area, length) and property attributes for all features in a file."
)
async def get_file_measurements(file_id: str) -> FileMeasurementsResponse:
    measurements = file_service.get_measurements(file_id)
    if not measurements:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Measurements for file ID '{file_id}' not found."
        )
    return measurements
