import os
import zipfile
import xml.etree.ElementTree as ET
from typing import Tuple, List, Dict, Any
import geopandas as gpd
from shapely.geometry import Point, LineString, Polygon, MultiPolygon, MultiLineString, MultiPoint, shape
from shapely.wkt import loads as parse_wkt
import fiona

from app.utils.validation import (
    validate_zip_shapefile_contents,
    CorruptedFileError,
    InvalidFileFormatError
)

# Enable KML driver in Fiona if supported
try:
    fiona.drvsupport.supported_drivers['KML'] = 'rw'
    fiona.drvsupport.supported_drivers['LIBKML'] = 'rw'
except Exception:
    pass


class GeospatialService:
    @staticmethod
    def load_geospatial_data(file_path: str, file_ext: str) -> gpd.GeoDataFrame:
        """
        Loads a KML or ZIP Shapefile into a GeoPandas GeoDataFrame.
        Raises CorruptedFileError or InvalidFileFormatError if unparseable.
        """
        if file_ext == ".zip":
            return GeospatialService._load_shapefile_from_zip(file_path)
        elif file_ext == ".kml":
            return GeospatialService._load_kml_file(file_path)
        else:
            raise InvalidFileFormatError(f"Unsupported file extension: {file_ext}")

    @staticmethod
    def _load_shapefile_from_zip(zip_path: str) -> gpd.GeoDataFrame:
        """Unpacks ZIP archive and reads contained Shapefile into GeoDataFrame."""
        shp_relative_path = validate_zip_shapefile_contents(zip_path)
        extract_dir = os.path.dirname(zip_path)

        try:
            with zipfile.ZipFile(zip_path, 'r') as zf:
                zf.extractall(extract_dir)

            full_shp_path = os.path.join(extract_dir, shp_relative_path)
            gdf = gpd.read_file(full_shp_path)

            if gdf.empty and len(gdf) == 0:
                # Still valid GeoDataFrame even if 0 rows, but let's ensure it loaded
                pass

            return gdf
        except Exception as e:
            raise CorruptedFileError(f"Failed to read Shapefile: {str(e)}")

    @staticmethod
    def _load_kml_file(kml_path: str) -> gpd.GeoDataFrame:
        """Reads KML file into GeoDataFrame using GeoPandas driver or custom KML XML parser fallback."""
        gdf = None
        # Method 1: Try reading directly via GeoPandas / Fiona drivers
        try:
            gdf = gpd.read_file(kml_path, driver="KML")
            if gdf is not None and not gdf.empty:
                if gdf.crs is None:
                    gdf.crs = "EPSG:4326"
                return gdf
        except Exception:
            pass

        try:
            gdf = gpd.read_file(kml_path, driver="LIBKML")
            if gdf is not None and not gdf.empty:
                if gdf.crs is None:
                    gdf.crs = "EPSG:4326"
                return gdf
        except Exception:
            pass

        # Method 2: Robust XML Placemark parser fallback for KML files
        return GeospatialService._parse_kml_xml_fallback(kml_path)

    @staticmethod
    def _parse_kml_xml_fallback(kml_path: str) -> gpd.GeoDataFrame:
        """
        Parses KML file using ElementTree XML parser to extract Placemarks into a GeoDataFrame.
        KML standard strictly specifies EPSG:4326 coordinates.
        """
        try:
            tree = ET.parse(kml_path)
            root = tree.getroot()
        except ET.ParseError as pe:
            raise CorruptedFileError(f"Invalid or corrupted KML XML format: {str(pe)}")

        # Handle KML namespaces (e.g. {http://www.opengis.net/kml/2.2})
        ns = ""
        if root.tag.startswith("{"):
            ns = root.tag.split("}")[0] + "}"

        records = []

        # Find all Placemark nodes recursively
        placemarks = root.findall(f".//{ns}Placemark")

        for idx, pm in enumerate(placemarks):
            name_node = pm.find(f"{ns}name")
            desc_node = pm.find(f"{ns}description")
            name = name_node.text if name_node is not None else f"Feature_{idx}"
            desc = desc_node.text if desc_node is not None else ""

            props = {"name": name, "description": desc}

            # Parse ExtendedData SimpleData if present
            for sd in pm.findall(f".//{ns}SimpleData"):
                attr_name = sd.attrib.get("name")
                if attr_name:
                    props[attr_name] = sd.text

            geom = None

            # 1. Polygon
            poly_node = pm.find(f".//{ns}Polygon")
            if poly_node is not None:
                coord_node = poly_node.find(f".//{ns}coordinates")
                if coord_node is not None and coord_node.text:
                    coords = GeospatialService._parse_kml_coords(coord_node.text)
                    if len(coords) >= 3:
                        geom = Polygon(coords)

            # 2. LineString
            if geom is None:
                ls_node = pm.find(f".//{ns}LineString")
                if ls_node is not None:
                    coord_node = ls_node.find(f".//{ns}coordinates")
                    if coord_node is not None and coord_node.text:
                        coords = GeospatialService._parse_kml_coords(coord_node.text)
                        if len(coords) >= 2:
                            geom = LineString(coords)

            # 3. Point
            if geom is None:
                pt_node = pm.find(f".//{ns}Point")
                if pt_node is not None:
                    coord_node = pt_node.find(f".//{ns}coordinates")
                    if coord_node is not None and coord_node.text:
                        coords = GeospatialService._parse_kml_coords(coord_node.text)
                        if coords:
                            geom = Point(coords[0])

            if geom is not None:
                props["geometry"] = geom
                records.append(props)

        if not records:
            raise CorruptedFileError("KML file contains no valid or readable feature geometries.")

        gdf = gpd.GeoDataFrame(records, crs="EPSG:4326")
        if "geometry" in gdf.columns:
            gdf = gdf.set_geometry("geometry")
        return gdf

    @staticmethod
    def _parse_kml_coords(text: str) -> List[Tuple[float, float]]:
        """Parses coordinate strings from KML format (lon,lat,alt or lon,lat)."""
        coords = []
        raw_tuples = text.strip().split()
        for item in raw_tuples:
            parts = item.split(",")
            if len(parts) >= 2:
                try:
                    lon = float(parts[0])
                    lat = float(parts[1])
                    coords.append((lon, lat))
                except ValueError:
                    continue
        return coords

    @staticmethod
    def extract_crs_name(gdf: gpd.GeoDataFrame) -> str:
        """Returns clean CRS name string (e.g. EPSG:4326) or default if missing."""
        if gdf.crs is None:
            return "EPSG:4326 (Default)"
        try:
            epsg = gdf.crs.to_epsg()
            if epsg:
                return f"EPSG:{epsg}"
            return str(gdf.crs.to_string())
        except Exception:
            return str(gdf.crs)
