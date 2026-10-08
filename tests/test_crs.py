import pytest
import geopandas as gpd
from shapely.geometry import Polygon
from app.services.measurement_service import MeasurementService


def test_utm_zone_lookup():
    # New Delhi, India (Lon: 77.2090, Lat: 28.6139) -> UTM Zone 43N -> EPSG:32643
    epsg_code, epsg_str = MeasurementService.get_utm_epsg_for_latlon(77.2090, 28.6139)
    assert epsg_code == 32643
    assert epsg_str == "EPSG:32643"

    # Sydney, Australia (Lon: 151.2093, Lat: -33.8688) -> UTM Zone 56S -> EPSG:32756
    epsg_code_syd, epsg_str_syd = MeasurementService.get_utm_epsg_for_latlon(151.2093, -33.8688)
    assert epsg_code_syd == 32756
    assert epsg_str_syd == "EPSG:32756"


def test_geographic_crs_transformation():
    # 0.01 degree x 0.01 degree square in geographic coordinates EPSG:4326
    # Raw degree area would be 0.0001 (degrees squared), which is physically meaningless for real-world area.
    poly_deg = Polygon([(77.20, 28.61), (77.21, 28.61), (77.21, 28.62), (77.20, 28.62), (77.20, 28.61)])
    raw_deg_area = poly_deg.area
    assert raw_deg_area == pytest.approx(0.0001, abs=1e-5)

    gdf = gpd.GeoDataFrame([{"geometry": poly_deg}], crs="EPSG:4326")
    measurements = MeasurementService.process_gdf_measurements(gdf)

    assert len(measurements) == 1
    item = measurements[0]
    # Projected area should be in square meters (approx 1 sq km = ~1,000,000 sq meters)
    assert item.projected_crs == "EPSG:32643"
    assert item.area is not None
    assert item.area > 500000  # Definitely in square meters, not angular degrees!
    assert item.area_unit == "square meters"
