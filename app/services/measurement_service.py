import math
from typing import Dict, List, Optional, Tuple, Any
import geopandas as gpd
import pyproj
from pyproj import CRS
from shapely.geometry import base, Point, LineString, Polygon, MultiPolygon, MultiLineString, MultiPoint

from app.models.schemas import MeasurementItem
from app.services.geospatial_service import GeospatialService


class MeasurementService:
    @staticmethod
    def get_utm_epsg_for_latlon(lon: float, lat: float) -> Tuple[int, str]:
        """
        Determines the appropriate UTM EPSG code for a given longitude and latitude.
        UTM zones are 6-degree wide strips.
        EPSG:32601 - 32660 for Northern Hemisphere (lat >= 0)
        EPSG:32701 - 32760 for Southern Hemisphere (lat < 0)
        """
        lat = max(-80.0, min(84.0, lat))
        lon = ((lon + 180) % 360) - 180

        zone_number = int((lon + 180) / 6) + 1
        zone_number = max(1, min(60, zone_number))

        if lat >= 0:
            epsg_code = 32600 + zone_number
        else:
            epsg_code = 32700 + zone_number

        return epsg_code, f"EPSG:{epsg_code}"

    @staticmethod
    def get_projected_crs_for_gdf(gdf: gpd.GeoDataFrame) -> Tuple[CRS, str]:
        """
        Determines an appropriate projected CRS for measurement calculations.
        If dataset is geographic (e.g. EPSG:4326), computes UTM zone based on centroid.
        """
        if gdf.crs is not None and gdf.crs.is_projected:
            return gdf.crs, GeospatialService.extract_crs_name(gdf)

        if len(gdf) == 0:
            return CRS.from_epsg(32643), "EPSG:32643"

        try:
            bounds = gdf.total_bounds  # [minx, miny, maxx, maxy]
            if not math.isfinite(bounds[0]) or not math.isfinite(bounds[1]):
                center_lon, center_lat = 0.0, 0.0
            else:
                center_lon = (bounds[0] + bounds[2]) / 2.0
                center_lat = (bounds[1] + bounds[3]) / 2.0
        except Exception:
            center_lon, center_lat = 0.0, 0.0

        epsg_int, epsg_str = MeasurementService.get_utm_epsg_for_latlon(center_lon, center_lat)
        projected_crs = CRS.from_epsg(epsg_int)
        return projected_crs, epsg_str

    @staticmethod
    def process_gdf_measurements(gdf: gpd.GeoDataFrame) -> List[MeasurementItem]:
        """
        Processes all features in a GeoDataFrame:
        1. Identifies source CRS and appropriate Projected CRS (UTM).
        2. Reprojects GeoDataFrame into projected CRS for accurate metric area & length calculations.
        3. Computes area (Polygon/MultiPolygon) or length (LineString/MultiLineString).
        4. Handles Points and unsupported geometries gracefully.
        5. Preserves feature attributes.
        """
        source_crs_str = GeospatialService.extract_crs_name(gdf)

        # Ensure source CRS is set on GeoDataFrame (default EPSG:4326 if missing)
        if gdf.crs is None:
            gdf = gdf.set_crs("EPSG:4326")

        # Determine projected CRS
        projected_crs, projected_crs_str = MeasurementService.get_projected_crs_for_gdf(gdf)

        # Reproject GeoDataFrame using native GeoPandas to_crs
        reproject_required = (gdf.crs != projected_crs)
        if reproject_required:
            try:
                projected_gdf = gdf.to_crs(projected_crs)
            except Exception:
                projected_gdf = gdf
        else:
            projected_gdf = gdf

        measurements: List[MeasurementItem] = []

        geom_col = gdf.geometry.name if hasattr(gdf, "geometry") and gdf.geometry.name in gdf.columns else "geometry"
        attribute_cols = [col for col in gdf.columns if col != geom_col]

        for idx in range(len(gdf)):
            row = gdf.iloc[idx]
            proj_row = projected_gdf.iloc[idx]

            geom = row[geom_col] if geom_col in row else None
            proj_geom = proj_row[geom_col] if geom_col in proj_row else geom

            # Extract non-geometry attributes as clean dictionary
            properties: Dict[str, Any] = {}
            for col in attribute_cols:
                val = row[col]
                if hasattr(val, "item"):
                    val = val.item()
                elif type(val).__name__ in ["Timestamp", "Timedelta", "NaTType"]:
                    val = None if str(val) in ["NaT", "nan"] else str(val)
                elif isinstance(val, float) and (math.isnan(val) or math.isinf(val)):
                    val = None
                elif isinstance(val, (float, int, str, bool)) or val is None:
                    pass
                else:
                    s_val = str(val)
                    val = None if s_val in ["NaT", "nan", "<NA>", "None"] else s_val
                if val is not None:
                    properties[col] = val

            if geom is None or geom.is_empty:
                measurements.append(MeasurementItem(
                    feature_id=int(idx),
                    geometry_type="Empty/Null",
                    area=None,
                    area_unit=None,
                    length=None,
                    length_unit=None,
                    measurement_status="Empty Geometry",
                    source_crs=source_crs_str,
                    projected_crs=projected_crs_str if reproject_required else None,
                    properties=properties
                ))
                continue

            geom_type = geom.geom_type

            area_val: Optional[float] = None
            area_unit_str: Optional[str] = None
            length_val: Optional[float] = None
            length_unit_str: Optional[str] = None
            status_str = "Calculated"

            if geom_type in ["Polygon", "MultiPolygon"]:
                area_val = round(float(proj_geom.area), 2)
                area_unit_str = "square meters"
            elif geom_type in ["LineString", "MultiLineString"]:
                length_val = round(float(proj_geom.length), 2)
                length_unit_str = "meters"
            elif geom_type in ["Point", "MultiPoint"]:
                status_str = "N/A - Point Geometry"
            else:
                status_str = f"Unsupported Geometry ({geom_type})"

            measurements.append(MeasurementItem(
                feature_id=int(idx),
                geometry_type=geom_type,
                area=area_val,
                area_unit=area_unit_str,
                length=length_val,
                length_unit=length_unit_str,
                measurement_status=status_str,
                source_crs=source_crs_str,
                projected_crs=projected_crs_str if reproject_required else None,
                properties=properties
            ))

        return measurements
