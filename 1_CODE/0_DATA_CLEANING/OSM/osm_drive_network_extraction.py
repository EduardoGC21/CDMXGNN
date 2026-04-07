from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import geopandas as gpd
import osmnx as ox
import pandas as pd
from pandas.api.types import is_object_dtype, is_string_dtype
from pyproj import CRS
from shapely.geometry import box
from unidecode import unidecode

PLACE_QUERY = "Ciudad de Mexico, CDMX, Mexico"
NETWORK_TYPE = "drive"
INTERSECTION_STREET_COUNT_THRESHOLD = 2
DEFAULT_ENTITY_BOUNDARY_PATH = (
    Path(__file__).resolve().parents[3]
    / "0_DATA"
    / "1_CLEAN"
    / "MGE"
    / "entidad_cdmx.parquet"
)
DEFAULT_MUNICIPIOS_BOUNDARY_PATH = (
    Path(__file__).resolve().parents[3]
    / "0_DATA"
    / "1_CLEAN"
    / "MGE"
    / "municipios_cdmx.parquet"
)
DEFAULT_OUTPUT_DIR = (
    Path(__file__).resolve().parents[3]
    / "0_DATA"
    / "0_RAW"
    / "OSM"
    / "drive_network"
)
DEFAULT_DENUE_BOUNDARY_FALLBACK_PATH = (
    Path(__file__).resolve().parents[3]
    / "0_DATA"
    / "1_CLEAN"
    / "INEGI"
    / "DENUE"
    / "denue_clean.parquet"
)


def standardize_string(value: Any) -> Any:
    if pd.isna(value):
        return value

    normalized = unidecode(str(value)).lower().strip()
    normalized = re.sub(r"[^\w\s]", "_", normalized)
    normalized = re.sub(r"\s+", "_", normalized)
    normalized = re.sub(r"_+", "_", normalized)
    normalized = normalized.strip("_")
    return normalized


def standardize_columns(df: pd.DataFrame) -> pd.DataFrame:
    renamed = {column: standardize_string(column) for column in df.columns}
    return df.rename(columns=renamed)


def serialize_value(value: Any) -> Any:
    if isinstance(value, (list, tuple, dict, set)):
        return json.dumps(value, ensure_ascii=True, sort_keys=True, default=str)
    if value is None:
        return pd.NA
    if pd.isna(value):
        return pd.NA
    return value


def serialize_complex_columns(df: pd.DataFrame) -> pd.DataFrame:
    geometry_columns = {
        column
        for column in df.columns
        if getattr(df[column].dtype, "name", "") == "geometry"
    }

    for column in df.columns:
        if column in geometry_columns:
            continue
        if not (is_string_dtype(df[column]) or is_object_dtype(df[column])):
            continue
        df[column] = df[column].map(serialize_value)

    for column in df.columns:
        if column in geometry_columns:
            continue
        if is_object_dtype(df[column]):
            df[column] = df[column].astype("string")
    return df


def load_denue_bounds_boundary(denue_path: str | Path = DEFAULT_DENUE_BOUNDARY_FALLBACK_PATH):
    denue_path = Path(denue_path)
    denue = gpd.read_parquet(denue_path)
    if denue.crs is None:
        raise ValueError("DENUE fallback boundary has no CRS.")

    denue = denue.to_crs("EPSG:4326")
    minx, miny, maxx, maxy = denue.total_bounds
    return box(minx, miny, maxx, maxy)


def load_boundary_from_parquet(boundary_path: str | Path) -> Any:
    boundary_path = Path(boundary_path)
    boundary_gdf = gpd.read_parquet(boundary_path)
    if boundary_gdf.crs is None:
        raise ValueError(f"Boundary layer has no CRS: {boundary_path}")
    return boundary_gdf.to_crs("EPSG:4326").union_all()


def load_cdmx_boundary(
    entity_boundary_path: str | Path = DEFAULT_ENTITY_BOUNDARY_PATH,
    municipios_boundary_path: str | Path = DEFAULT_MUNICIPIOS_BOUNDARY_PATH,
) -> tuple[Any, str]:
    entity_boundary_path = Path(entity_boundary_path)
    municipios_boundary_path = Path(municipios_boundary_path)

    if entity_boundary_path.exists():
        try:
            boundary = load_boundary_from_parquet(entity_boundary_path)
            return boundary, str(entity_boundary_path)
        except Exception:
            pass

    if municipios_boundary_path.exists():
        try:
            boundary = load_boundary_from_parquet(municipios_boundary_path)
            return boundary, str(municipios_boundary_path)
        except Exception:
            pass

    try:
        boundary = load_denue_bounds_boundary()
        return boundary, f"denue_bounds:{DEFAULT_DENUE_BOUNDARY_FALLBACK_PATH}"
    except Exception:
        pass

    place_gdf = ox.geocode_to_gdf(PLACE_QUERY)
    if place_gdf.empty:
        raise ValueError(f"Could not geocode OSM boundary for {PLACE_QUERY}.")
    boundary = place_gdf.to_crs("EPSG:4326").union_all()
    return boundary, f"osm_geocode:{PLACE_QUERY}"


def graph_to_tables(graph) -> tuple[gpd.GeoDataFrame, gpd.GeoDataFrame, gpd.GeoDataFrame]:
    nodes_gdf, edges_gdf = ox.graph_to_gdfs(graph, nodes=True, edges=True, fill_edge_geometry=True)

    nodes_gdf = nodes_gdf.reset_index(names="osmid")
    edges_gdf = edges_gdf.reset_index(names=["u", "v", "key"])

    nodes_gdf = standardize_columns(nodes_gdf)
    edges_gdf = standardize_columns(edges_gdf)
    nodes_gdf = serialize_complex_columns(nodes_gdf)
    edges_gdf = serialize_complex_columns(edges_gdf)

    if "street_count" in nodes_gdf.columns:
        intersections_gdf = nodes_gdf.loc[
            nodes_gdf["street_count"].fillna(0) >= INTERSECTION_STREET_COUNT_THRESHOLD
        ].copy()
    else:
        intersections_gdf = nodes_gdf.copy()

    return nodes_gdf, edges_gdf, intersections_gdf


def build_summary(
    graph,
    nodes_gdf: gpd.GeoDataFrame,
    edges_gdf: gpd.GeoDataFrame,
    intersections_gdf: gpd.GeoDataFrame,
    boundary_source: str,
    output_dir: Path,
) -> dict[str, Any]:
    graph_crs = CRS.from_user_input(graph.graph["crs"]).to_string()
    return {
        "boundary_source": boundary_source,
        "network_type": NETWORK_TYPE,
        "graph_crs": graph_crs,
        "node_count": len(nodes_gdf),
        "edge_count": len(edges_gdf),
        "intersection_count": len(intersections_gdf),
        "output_dir": str(output_dir),
    }


def extract_osm_drive_network(
    entity_boundary_path: str | Path = DEFAULT_ENTITY_BOUNDARY_PATH,
    municipios_boundary_path: str | Path = DEFAULT_MUNICIPIOS_BOUNDARY_PATH,
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
) -> tuple[dict[str, Path], dict[str, Any]]:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    ox.settings.use_cache = True
    ox.settings.log_console = False

    boundary, boundary_source = load_cdmx_boundary(
        entity_boundary_path=entity_boundary_path,
        municipios_boundary_path=municipios_boundary_path,
    )
    graph = ox.graph_from_polygon(
        boundary,
        network_type=NETWORK_TYPE,
        simplify=True,
        retain_all=True,
        truncate_by_edge=True,
    )

    nodes_gdf, edges_gdf, intersections_gdf = graph_to_tables(graph)

    graphml_path = output_dir / "cdmx_drive_graph.graphml"
    nodes_path = output_dir / "cdmx_drive_nodes_raw.parquet"
    edges_path = output_dir / "cdmx_drive_edges_raw.parquet"
    intersections_path = output_dir / "cdmx_drive_intersections_raw.parquet"

    ox.save_graphml(graph, filepath=graphml_path)
    nodes_gdf.to_parquet(nodes_path)
    edges_gdf.to_parquet(edges_path)
    intersections_gdf.to_parquet(intersections_path)

    output_paths = {
        "graphml": graphml_path,
        "nodes": nodes_path,
        "edges": edges_path,
        "intersections": intersections_path,
    }
    summary = build_summary(
        graph=graph,
        nodes_gdf=nodes_gdf,
        edges_gdf=edges_gdf,
        intersections_gdf=intersections_gdf,
        boundary_source=boundary_source,
        output_dir=output_dir,
    )
    return output_paths, summary


if __name__ == "__main__":
    output_paths, summary = extract_osm_drive_network()
    print(f"Saved OSM drive network raw outputs to {summary['output_dir']}")
    print(f"Boundary source: {summary['boundary_source']}")
    print(f"Network type: {summary['network_type']}")
    print(f"Graph CRS: {summary['graph_crs']}")
    print(f"Nodes: {summary['node_count']:,}")
    print(f"Edges: {summary['edge_count']:,}")
    print(
        f"Intersection candidates (street_count >= {INTERSECTION_STREET_COUNT_THRESHOLD}): "
        f"{summary['intersection_count']:,}"
    )
    print("Files:")
    for name, path in output_paths.items():
        print(f"  - {name}: {path}")
