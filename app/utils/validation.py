import os
import zipfile
from typing import List, Tuple

ALLOWED_EXTENSIONS = {".kml", ".zip"}
MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024  # 50 MB limit


class ValidationError(Exception):
    """Base exception for file validation errors."""
    def __init__(self, message: str, error_code: str = "VALIDATION_ERROR"):
        super().__init__(message)
        self.message = message
        self.error_code = error_code


class InvalidFileFormatError(ValidationError):
    def __init__(self, message: str):
        super().__init__(message, error_code="UNSUPPORTED_FILE_TYPE")


class CorruptedFileError(ValidationError):
    def __init__(self, message: str):
        super().__init__(message, error_code="CORRUPTED_FILE")


class MissingShapefileComponentError(ValidationError):
    def __init__(self, message: str):
        super().__init__(message, error_code="MISSING_SHAPEFILE_COMPONENTS")


def validate_file_extension(filename: str) -> str:
    """
    Validates that the file has a supported extension (.kml or .zip).
    Returns lower-case extension.
    """
    if not filename:
        raise InvalidFileFormatError("Filename is empty or missing.")

    ext = os.path.splitext(filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise InvalidFileFormatError(
            f"Unsupported file format '{ext}'. Allowed formats are: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
        )
    return ext


def validate_file_size(content: bytes) -> None:
    """
    Validates file size (not empty and not exceeding maximum size limit).
    """
    if not content or len(content) == 0:
        raise CorruptedFileError("Uploaded file is empty (0 bytes).")
    if len(content) > MAX_FILE_SIZE_BYTES:
        raise ValidationError(
            f"File size exceeds maximum allowed limit of {MAX_FILE_SIZE_BYTES // (1024 * 1024)}MB."
        )


def validate_zip_shapefile_contents(zip_path: str) -> str:
    """
    Validates a ZIP archive:
    1. Checks if it is a valid, un-corrupted ZIP file.
    2. Prevents path traversal security vulnerabilities (Zip Slip).
    3. Ensures a .shp file is present along with required components (.shx, .dbf).
    
    Returns the relative path inside the ZIP to the primary .shp file.
    """
    if not zipfile.is_zipfile(zip_path):
        raise CorruptedFileError("The uploaded file is not a valid or readable ZIP archive.")

    try:
        with zipfile.ZipFile(zip_path, 'r') as zf:
            file_list = zf.namelist()

            # Path traversal safety check
            for name in file_list:
                # Prevent absolute paths or directory traversal elements
                normalized = os.path.normpath(name)
                if normalized.startswith("..") or os.path.isabs(name) or name.startswith("/") or name.startswith("\\"):
                    raise ValidationError("ZIP archive contains unsafe path entries (Path Traversal detected).")

            # Find .shp files
            shp_files = [f for f in file_list if f.lower().endswith(".shp") and not f.startswith("__MACOSX")]

            if not shp_files:
                raise MissingShapefileComponentError(
                    "ZIP archive does not contain a Shapefile (.shp file)."
                )

            # Pick the primary .shp file (first one found if multiple)
            primary_shp = shp_files[0]
            base_prefix = os.path.splitext(primary_shp)[0]

            # Required shapefile components: .shp, .shx, .dbf
            required_extensions = [".shp", ".shx", ".dbf"]
            missing = []

            for ext in required_extensions:
                expected_file = base_prefix + ext
                # Case-insensitive check
                matching = [f for f in file_list if f.lower() == expected_file.lower()]
                if not matching:
                    missing.append(ext)

            if missing:
                raise MissingShapefileComponentError(
                    f"Shapefile in ZIP is missing required component files: {', '.join(missing)}"
                )

            return primary_shp

    except zipfile.BadZipFile:
        raise CorruptedFileError("The uploaded ZIP file is corrupted and cannot be opened.")
