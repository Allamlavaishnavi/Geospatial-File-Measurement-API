import io
import os
import zipfile
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

SAMPLE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "sample_data"))


def test_upload_valid_kml():
    kml_path = os.path.join(SAMPLE_DIR, "polygon.kml")
    with open(kml_path, "rb") as f:
        response = client.post("/api/files/", files={"file": ("polygon.kml", f, "application/vnd.google-earth.kml+xml")})
    
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["filename"] == "polygon.kml"
    assert data["feature_count"] >= 1
    assert data["status"] == "COMPLETED"
    assert "EPSG" in data["crs"]

    # Test GET summary endpoint
    file_id = data["id"]
    get_res = client.get(f"/api/files/{file_id}/")
    assert get_res.status_code == 200
    assert get_res.json()["id"] == file_id

    # Test GET measurements endpoint
    meas_res = client.get(f"/api/files/{file_id}/measurements/")
    assert meas_res.status_code == 200
    meas_data = meas_res.json()
    assert meas_data["file_id"] == file_id
    assert len(meas_data["measurements"]) >= 1
    first_meas = meas_data["measurements"][0]
    assert first_meas["geometry_type"] == "Polygon"
    assert first_meas["area"] is not None
    assert first_meas["area_unit"] == "square meters"


def test_upload_valid_shapefile_zip():
    zip_path = os.path.join(SAMPLE_DIR, "shapefile.zip")
    with open(zip_path, "rb") as f:
        response = client.post("/api/files/", files={"file": ("shapefile.zip", f, "application/zip")})
    
    assert response.status_code == 201
    data = response.json()
    assert data["filename"] == "shapefile.zip"
    assert data["status"] == "COMPLETED"

    file_id = data["id"]
    meas_res = client.get(f"/api/files/{file_id}/measurements/")
    assert meas_res.status_code == 200
    assert len(meas_res.json()["measurements"]) >= 1


def test_upload_unsupported_extension():
    fake_file = io.BytesIO(b"dummy text content")
    response = client.post("/api/files/", files={"file": ("test.txt", fake_file, "text/plain")})
    assert response.status_code == 400
    assert "Unsupported file format" in response.json()["detail"]


def test_upload_empty_file():
    empty_file = io.BytesIO(b"")
    response = client.post("/api/files/", files={"file": ("empty.kml", empty_file, "application/xml")})
    assert response.status_code == 400
    assert "empty" in response.json()["detail"].lower()


def test_upload_corrupted_kml():
    corrupted_kml = io.BytesIO(b"<?xml version='1.0'?><kml><Document><Placemark><Polygon><coordinates>INVALID DATA</coordinates></Polygon></Placemark></Document></kml>")
    response = client.post("/api/files/", files={"file": ("corrupted.kml", corrupted_kml, "application/xml")})
    # Should handle cleanly with 400 error or empty feature result
    assert response.status_code in [201, 400]


def test_upload_invalid_zip():
    fake_zip = io.BytesIO(b"This is not a zip file content")
    response = client.post("/api/files/", files={"file": ("bad.zip", fake_zip, "application/zip")})
    assert response.status_code == 400
    assert "ZIP archive" in response.json()["detail"] or "valid" in response.json()["detail"].lower()


def test_upload_zip_without_shapefile():
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w') as zf:
        zf.writestr("read_me.txt", "No shapefile in this zip")
    zip_buffer.seek(0)

    response = client.post("/api/files/", files={"file": ("noshp.zip", zip_buffer, "application/zip")})
    assert response.status_code == 400
    assert "Shapefile" in response.json()["detail"]


def test_get_nonexistent_file_summary():
    response = client.get("/api/files/nonexistent_id/")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_get_nonexistent_file_measurements():
    response = client.get("/api/files/nonexistent_id/measurements/")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()
