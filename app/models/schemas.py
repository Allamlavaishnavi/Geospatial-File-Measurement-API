from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class FileStatusEnum(str, Enum):
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class FileSummaryResponse(BaseModel):
    id: str = Field(..., description="Unique file identifier", json_schema_extra={"example": "abc12345"})
    filename: str = Field(..., description="Original name of uploaded file", json_schema_extra={"example": "survey.kml"})
    feature_count: int = Field(..., description="Total number of features in file", json_schema_extra={"example": 12})
    crs: str = Field(..., description="Coordinate Reference System of source data", json_schema_extra={"example": "EPSG:4326"})
    status: FileStatusEnum = Field(..., description="Processing status", json_schema_extra={"example": "COMPLETED"})
    created_at: str = Field(..., description="Timestamp of file upload")
    error_message: Optional[str] = Field(None, description="Error details if processing failed")


class MeasurementItem(BaseModel):
    feature_id: int = Field(..., description="Index/ID of the feature", json_schema_extra={"example": 0})
    geometry_type: str = Field(..., description="Geometry type name", json_schema_extra={"example": "Polygon"})
    area: Optional[float] = Field(None, description="Calculated area in square meters (if applicable)", json_schema_extra={"example": 12345.67})
    area_unit: Optional[str] = Field(None, description="Unit of area measurement", json_schema_extra={"example": "square meters"})
    length: Optional[float] = Field(None, description="Calculated length in meters (if applicable)", json_schema_extra={"example": 1250.45})
    length_unit: Optional[str] = Field(None, description="Unit of length measurement", json_schema_extra={"example": "meters"})
    measurement_status: str = Field(..., description="Status of measurement calculation", json_schema_extra={"example": "Calculated"})
    source_crs: str = Field(..., description="Source CRS of geometry", json_schema_extra={"example": "EPSG:4326"})
    projected_crs: Optional[str] = Field(None, description="Projected CRS used for measurement", json_schema_extra={"example": "EPSG:32643"})
    properties: Dict[str, Any] = Field(default_factory=dict, description="Attributes/properties of the feature")


class FileMeasurementsResponse(BaseModel):
    file_id: str = Field(..., description="Unique file identifier", json_schema_extra={"example": "abc12345"})
    filename: str = Field(..., description="Original name of uploaded file", json_schema_extra={"example": "survey.kml"})
    feature_count: int = Field(..., description="Total number of features", json_schema_extra={"example": 12})
    measurements: List[MeasurementItem] = Field(default_factory=list, description="List of feature measurements")


class ErrorResponse(BaseModel):
    detail: str = Field(..., description="Human readable error message")
    error_code: str = Field(..., description="Machine readable error code", json_schema_extra={"example": "INVALID_FILE_TYPE"})
