import io
import os
import zipfile
import pytest
from app.utils.validation import (
    validate_file_extension,
    validate_file_size,
    validate_zip_shapefile_contents,
    InvalidFileFormatError,
    CorruptedFileError,
    ValidationError
)


def test_validate_file_extension_valid():
    assert validate_file_extension("survey.kml") == ".kml"
    assert validate_file_extension("data.ZIP") == ".zip"


def test_validate_file_extension_invalid():
    with pytest.raises(InvalidFileFormatError):
        validate_file_extension("data.geojson")
    with pytest.raises(InvalidFileFormatError):
        validate_file_extension("data.csv")


def test_validate_file_size():
    with pytest.raises(CorruptedFileError):
        validate_file_size(b"")

    # Valid non-empty size
    validate_file_size(b"some content")


def test_zip_path_traversal_prevention(tmp_path):
    # Create a malicious zip file containing path traversal entry
    malicious_zip = tmp_path / "malicious.zip"
    with zipfile.ZipFile(malicious_zip, 'w') as zf:
        zf.writestr("../evil.txt", "exploit")
        zf.writestr("test.shp", "shapefile")
        zf.writestr("test.shx", "shx index")
        zf.writestr("test.dbf", "dbf table")

    with pytest.raises(ValidationError) as excinfo:
        validate_zip_shapefile_contents(str(malicious_zip))
    assert "Path Traversal" in str(excinfo.value)
