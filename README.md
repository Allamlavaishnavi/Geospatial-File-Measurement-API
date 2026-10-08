# Geospatial File Measurement API 🌍📏

A complete, clean, and robust backend REST API built with **FastAPI**, **GeoPandas**, **PyProj**, and **Shapely** to process geospatial files (`.kml` and Shapefile `.zip`), extract vector features, handle Coordinate Reference Systems (CRS) dynamically, and compute accurate geometric measurements.

---

## 📌 Project Overview

Geospatial vector files (such as Keyhole Markup Language `.kml` or ESRI Shapefiles `.zip`) store spatial geometries like Polygons, LineStrings, and Points. However, geographic coordinate reference systems like **EPSG:4326** represent locations in angular degrees (latitude/longitude), making direct Euclidean area or length calculations inaccurate.

This service solves that problem by:
1. Parsing `.kml` files and Shapefile `.zip` archives.
2. Detecting source CRS metadata.
3. Dynamically computing the optimal projected coordinate reference system (such as **UTM Zone Projections**) based on feature location.
4. Reprojecting geometries into metric projected units.
5. Computing precise areas in **square meters** and lengths in **meters** while gracefully handling Points and unsupported geometry types.

---

## ✨ Features

- **Supported File Formats**: Keyhole Markup Language (`.kml`) & ESRI Shapefile Archives (`.zip`).
- **Feature & Attribute Extraction**: Extracts geometry type, coordinate bounds, CRS, and feature property attributes.
- **Dynamic CRS Transformation**: Transforms geographic coordinates (`EPSG:4326`) into metric projected CRS (**UTM**) before calculating measurements.
- **Geometric Measurement Calculations**:
  - **Polygon / MultiPolygon** → Area in `square meters` ($m^2$)
  - **LineString / MultiLineString** → Length in `meters` ($m$)
  - **Point / MultiPoint** → No area/length calculated (`N/A - Point Geometry`)
- **Robust Security & Validation**: Path traversal protection (Zip Slip prevention), file extension validation, corruption checks, and component verification (`.shp`, `.shx`, `.dbf`).
- **Interactive Swagger Documentation**: Built-in interactive documentation at `/docs`.
- **Automated Test Suite**: Full `pytest` coverage for upload, validation, CRS reprojection, and measurements.

---

## 🛠 Tech Stack

- **Language**: Python 3.13+
- **Framework**: FastAPI
- **Web Server**: Uvicorn
- **Geospatial Processing**: GeoPandas, Shapely, PyProj, Fiona
- **Validation & Serialization**: Pydantic v2, Python-Multipart
- **Automated Testing**: Pytest, HTTPX

---

## 📁 Project Structure

```text
geospatial-file-measurement-api/
│
├── app/
│   ├── __init__.py
│   ├── main.py                    # FastAPI app setup, OpenAPI configuration & error handlers
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes.py              # REST API route handlers
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── file_service.py        # In-memory storage & upload path manager
│   │   ├── geospatial_service.py  # KML & Shapefile GeoDataFrame loaders
│   │   └── measurement_service.py # Dynamic UTM CRS conversion & spatial math
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py             # Pydantic response models & status enums
│   │
│   └── utils/
│       ├── __init__.py
│       └── validation.py          # File extension, size & Zip security validators
│
├── tests/
│   ├── test_upload.py             # API upload & retrieval test cases
│   ├── test_measurements.py       # Spatial geometry measurement test cases
│   ├── test_crs.py                # CRS reprojection & UTM lookup test cases
│   └── test_validation.py         # Security & input validation test cases
│
├── sample_data/
│   ├── polygon.kml                # Sample polygon KML file
│   ├── lines.kml                  # Sample line KML file
│   ├── points.kml                 # Sample point KML file
│   └── shapefile.zip              # Sample Shapefile ZIP archive
│
├── uploads/                       # Storage for processed file uploads
├── requirements.txt               # Python package dependencies
├── README.md                      # Comprehensive project documentation
├── .gitignore                     # Git exclusion rules
└── run.py                         # Application entrypoint script
```

---

## 🚀 Setup & How to Run Locally

### 1. Prerequisites
Ensure Python 3.10+ is installed on your machine.

### 2. Create Virtual Environment (Windows)
Open PowerShell or Command Prompt in the project root directory:

```bash
python -m venv venv
venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Run Application Server
Start the development server:

```bash
python run.py
```

The application will start at:
- **Interactive Swagger UI**: `http://127.0.0.1:8000/docs`
- **OpenAPI Schema**: `http://127.0.0.1:8000/openapi.json`

---

## 📡 API Documentation

### 1. Upload Geospatial File
- **HTTP Method**: `POST`
- **URL Path**: `/api/files/`
- **Content-Type**: `multipart/form-data`
- **Parameters**: `file` (UploadFile)

**Example Request (cURL)**:
```bash
curl -X POST "http://127.0.0.1:8000/api/files/" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@sample_data/polygon.kml"
```

**Example Response (`201 Created`)**:
```json
{
  "id": "a813365f",
  "filename": "polygon.kml",
  "feature_count": 1,
  "crs": "EPSG:4326",
  "status": "COMPLETED",
  "created_at": "2026-10-08T06:42:59.406881+00:00",
  "error_message": null
}
```

---

### 2. Get File Information & Summary
- **HTTP Method**: `GET`
- **URL Path**: `/api/files/{id}/`

**Example Request**:
```bash
curl -X GET "http://127.0.0.1:8000/api/files/a813365f/"
```

**Example Response (`200 OK`)**:
```json
{
  "id": "a813365f",
  "filename": "polygon.kml",
  "feature_count": 1,
  "crs": "EPSG:4326",
  "status": "COMPLETED",
  "created_at": "2026-10-08T06:42:59.406881+00:00",
  "error_message": null
}
```

---

### 3. Get Feature-Level Measurements
- **HTTP Method**: `GET`
- **URL Path**: `/api/files/{id}/measurements/`

**Example Request**:
```bash
curl -X GET "http://127.0.0.1:8000/api/files/a813365f/measurements/"
```

**Example Response (`200 OK`)**:
```json
{
  "file_id": "a813365f",
  "filename": "polygon.kml",
  "feature_count": 1,
  "measurements": [
    {
      "feature_id": 0,
      "geometry_type": "Polygon",
      "area": 1084234.31,
      "area_unit": "square meters",
      "length": null,
      "length_unit": null,
      "measurement_status": "Calculated",
      "source_crs": "EPSG:4326",
      "projected_crs": "EPSG:32643",
      "properties": {
        "Name": "Central Park Zone",
        "description": "Sample polygon for area measurement test"
      }
    }
  ]
}
```

---

## 🔄 File Processing & Measurement Flow

```text
User File Upload (.kml / .zip)
       │
       ▼
Validation & Security Layer
 (Extension, Size & Zip Slip path traversal check)
       │
       ▼
Geospatial Data Ingestion Layer
 (Fiona / GeoPandas driver + XML Placemark Fallback parser)
       │
       ▼
CRS Detection & Reprojection Engine
 (Source CRS check -> Bounding box centroid -> UTM Zone selection)
       │
       ▼
Spatial Measurement Processing
 (Polygon -> Area sq.m | LineString -> Length m | Point -> N/A)
       │
       ▼
In-Memory Store & Response Serialization
 (Pydantic DTO output for API consumer)
```

---

## 🗺 CRS Handling Explanation

### Why Geographic Coordinates (EPSG:4326) Cannot Be Used Directly
`EPSG:4326` (WGS84) stores points as longitude and latitude angular degrees on a spherical model of the Earth.
- $1^\circ$ of longitude varies from ~111 km at the Equator down to $0$ km at the Poles.
- Calculating Euclidean distance or area using $\Delta x^2 + \Delta y^2$ directly on degrees produces meaningless units ($\text{degrees}^2$), causing massive spatial distortion.

### Dynamic UTM Projected CRS Transformation Strategy
To provide accurate metric measurements:
1. **Source CRS Detection**: The API inspects the layer's CRS.
2. **Centroid Calculation**: Computes the bounding box center $(\text{lon}, \text{lat})$.
3. **UTM Zone Selection**: Determines the correct Universal Transverse Mercator (UTM) 6-degree strip zone:
   $$\text{Zone Number} = \lfloor \frac{\text{Longitude} + 180}{6} \rfloor + 1$$
   - Northern Hemisphere ($\text{Lat} \ge 0$): `EPSG:32601` to `EPSG:32660`
   - Southern Hemisphere ($\text{Lat} < 0$): `EPSG:32701` to `EPSG:32760`
4. **Metric Measurement**: Geometries are reprojected into the projected CRS where linear units are **meters**, producing accurate areas in **square meters** ($m^2$) and lengths in **meters** ($m$).

---

## 🧪 Automated Testing & Verification

### Running Automated Tests
Run the `pytest` test suite:

```bash
pytest -v
```

All 21 test cases cover:
- **File Uploads**: Valid KML, valid Shapefile ZIP, unsupported extensions, empty files, corrupted files, missing shapefile components.
- **Geometries**: Polygon/MultiPolygon area, LineString/MultiLineString length, Point handling, unsupported geometry handling.
- **CRS Logic**: EPSG:4326 detection, UTM zone calculation, reprojection, metric unit verification.
- **Security & Validation**: Zip slip path traversal attacks, size limits, format validation.

---

## 💡 Important Design Decisions

1. **Layered Modular Architecture**: Business logic is separated into `services`, data transport into `models` (Pydantic DTOs), validation into `utils`, and routing into `api`.
2. **Dual-Tier KML Ingestion**: Uses GeoPandas/Fiona drivers as primary loader with a standard library `xml.etree.ElementTree` KML Placemark parser as fallback to ensure 100% platform portability across operating systems.
3. **Thread-Safe Memory Store**: Keeps persistence lightweight without requiring external database dependencies.
4. **Security First**: Prevents path traversal vulnerabilities when expanding `.zip` archives.

---

## 🔮 Learning & Future Scope

- **Asynchronous File Processing**: For multi-gigabyte raster or vector files, task queues (e.g. Celery / BackgroundTasks) could process uploads asynchronously.
- **Persistent Database Integration**: Integrating PostgreSQL with **PostGIS** extension for spatial querying.
- **Custom Unit Conversions**: Allowing users to query measurements in acres, hectares, feet, or miles via query parameters (`?unit=acres`).
