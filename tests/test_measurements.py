import geopandas as gpd
from shapely.geometry import Polygon, MultiPolygon, LineString, MultiLineString, Point, MultiPoint, GeometryCollection
from app.services.measurement_service import MeasurementService


def test_polygon_area_measurement():
    # Square approximately 0.01 deg x 0.01 deg near New Delhi (lat ~28.61, lon ~77.20)
    poly = Polygon([(77.20, 28.61), (77.21, 28.61), (77.21, 28.62), (77.20, 28.62), (77.20, 28.61)])
    gdf = gpd.GeoDataFrame([{"name": "Polygon 1", "geometry": poly}], crs="EPSG:4326")

    measurements = MeasurementService.process_gdf_measurements(gdf)
    assert len(measurements) == 1
    item = measurements[0]
    assert item.geometry_type == "Polygon"
    assert item.area is not None
    assert item.area > 0
    assert item.area_unit == "square meters"
    assert item.length is None
    assert item.measurement_status == "Calculated"


def test_multipolygon_area_measurement():
    poly1 = Polygon([(77.20, 28.61), (77.21, 28.61), (77.21, 28.62), (77.20, 28.62), (77.20, 28.61)])
    poly2 = Polygon([(77.22, 28.63), (77.23, 28.63), (77.23, 28.64), (77.22, 28.64), (77.22, 28.63)])
    mpoly = MultiPolygon([poly1, poly2])
    gdf = gpd.GeoDataFrame([{"name": "MultiPoly", "geometry": mpoly}], crs="EPSG:4326")

    measurements = MeasurementService.process_gdf_measurements(gdf)
    assert len(measurements) == 1
    item = measurements[0]
    assert item.geometry_type == "MultiPolygon"
    assert item.area is not None
    assert item.area > 0
    assert item.area_unit == "square meters"


def test_linestring_length_measurement():
    line = LineString([(77.20, 28.61), (77.21, 28.62)])
    gdf = gpd.GeoDataFrame([{"name": "Line 1", "geometry": line}], crs="EPSG:4326")

    measurements = MeasurementService.process_gdf_measurements(gdf)
    assert len(measurements) == 1
    item = measurements[0]
    assert item.geometry_type == "LineString"
    assert item.length is not None
    assert item.length > 0
    assert item.length_unit == "meters"
    assert item.area is None
    assert item.measurement_status == "Calculated"


def test_multilinestring_length_measurement():
    line1 = LineString([(77.20, 28.61), (77.21, 28.62)])
    line2 = LineString([(77.22, 28.63), (77.23, 28.64)])
    mline = MultiLineString([line1, line2])
    gdf = gpd.GeoDataFrame([{"name": "MultiLine", "geometry": mline}], crs="EPSG:4326")

    measurements = MeasurementService.process_gdf_measurements(gdf)
    assert len(measurements) == 1
    item = measurements[0]
    assert item.geometry_type == "MultiLineString"
    assert item.length is not None
    assert item.length > 0
    assert item.length_unit == "meters"


def test_point_handling():
    pt = Point(77.2090, 28.6139)
    gdf = gpd.GeoDataFrame([{"name": "Point 1", "geometry": pt}], crs="EPSG:4326")

    measurements = MeasurementService.process_gdf_measurements(gdf)
    assert len(measurements) == 1
    item = measurements[0]
    assert item.geometry_type == "Point"
    assert item.area is None
    assert item.length is None
    assert item.measurement_status == "N/A - Point Geometry"


def test_unsupported_geometry_handling():
    gc = GeometryCollection([Point(77.20, 28.61), LineString([(77.20, 28.61), (77.21, 28.62)])])
    gdf = gpd.GeoDataFrame([{"name": "Collection", "geometry": gc}], crs="EPSG:4326")

    measurements = MeasurementService.process_gdf_measurements(gdf)
    assert len(measurements) == 1
    item = measurements[0]
    assert item.geometry_type == "GeometryCollection"
    assert item.area is None
    assert item.length is None
    assert "Unsupported" in item.measurement_status
