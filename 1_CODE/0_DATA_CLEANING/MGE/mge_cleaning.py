from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import geopandas as gpd
import pandas as pd
from pandas.api.types import is_object_dtype, is_string_dtype
from unidecode import unidecode

TARGET_CRS = "EPSG:6372"
DEFAULT_INPUT_DIR = (
    Path(__file__).resolve().parents[3]
    / "0_DATA"
    / "0_RAW"
    / "MGE"
    / "conjunto_de_datos"
)
DEFAULT_OUTPUT_DIR = (
    Path(__file__).resolve().parents[3]
    / "0_DATA"
    / "1_CLEAN"
    / "MGE"
)

LAYER_SPECS = {
    "entidad_cdmx": {
        "input_name": "09ent.shp",
        "output_name": "entidad_cdmx.parquet",
        "value_columns_to_normalize": ["nomgeo"],
        "output_columns": ["cvegeo", "cve_ent", "nomgeo", "geometry"],
    },
    "municipios_cdmx": {
        "input_name": "09mun.shp",
        "output_name": "municipios_cdmx.parquet",
        "value_columns_to_normalize": ["nomgeo"],
        "output_columns": ["cvegeo", "cve_ent", "cve_mun", "nomgeo", "geometry"],
    },
    "ageb_urbana_cdmx": {
        "input_name": "09a.shp",
        "output_name": "ageb_urbana_cdmx.parquet",
        "value_columns_to_normalize": [],
        "output_columns": ["cve_ent", "cve_mun", "cve_loc", "cve_ageb", "cvegeo", "geometry"],
    },
    "manzanas_cdmx": {
        "input_name": "09m.shp",
        "output_name": "manzanas_cdmx.parquet",
        "value_columns_to_normalize": ["ambito", "tipomza"],
        "output_columns": [
            "cvegeo",
            "cve_ent",
            "cve_mun",
            "cve_loc",
            "cve_ageb",
            "cve_mza",
            "ambito",
            "tipomza",
            "geometry",
        ],
    },
    "localidades_cdmx": {
        "input_name": "09l.shp",
        "output_name": "localidades_cdmx.parquet",
        "value_columns_to_normalize": ["nomgeo", "ambito"],
        "output_columns": ["cvegeo", "cve_ent", "cve_mun", "cve_loc", "nomgeo", "ambito", "geometry"],
    },
}


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


def standardize_string_values(
    df: pd.DataFrame,
    include_columns: list[str] | None = None,
) -> pd.DataFrame:
    target_columns = set(include_columns) if include_columns is not None else set(df.columns)
    geometry_columns = {
        column
        for column in df.columns
        if getattr(df[column].dtype, "name", "") == "geometry"
    }

    for column in df.columns:
        if column not in target_columns or column in geometry_columns:
            continue
        if not (is_string_dtype(df[column]) or is_object_dtype(df[column])):
            continue
        df[column] = df[column].map(standardize_string)
    return df


def clean_mge_layer(
    input_path: str | Path,
    output_path: str | Path,
    value_columns_to_normalize: list[str],
    output_columns: list[str],
) -> tuple[gpd.GeoDataFrame, dict[str, Any]]:
    input_path = Path(input_path)
    output_path = Path(output_path)

    gdf = gpd.read_file(input_path)
    gdf = standardize_columns(gdf)
    gdf = standardize_string_values(gdf, include_columns=value_columns_to_normalize)
    gdf = gdf.loc[:, output_columns].copy()
    gdf = gdf.to_crs(TARGET_CRS)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    gdf.to_parquet(output_path)

    summary = {
        "output_path": str(output_path),
        "rows": len(gdf),
        "columns": len(gdf.columns),
        "crs": str(gdf.crs),
        "dtypes": {column: str(dtype) for column, dtype in gdf.dtypes.items()},
    }
    return gdf, summary


def clean_mge(
    input_dir: str | Path = DEFAULT_INPUT_DIR,
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
) -> dict[str, dict[str, Any]]:
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)

    summaries: dict[str, dict[str, Any]] = {}

    for layer_name, spec in LAYER_SPECS.items():
        _, summary = clean_mge_layer(
            input_path=input_dir / spec["input_name"],
            output_path=output_dir / spec["output_name"],
            value_columns_to_normalize=spec["value_columns_to_normalize"],
            output_columns=spec["output_columns"],
        )
        summaries[layer_name] = summary

    return summaries


if __name__ == "__main__":
    summaries = clean_mge()

    for layer_name, summary in summaries.items():
        print(f"\nLayer: {layer_name}")
        print(f"  Output path: {summary['output_path']}")
        print(f"  Rows: {summary['rows']:,}")
        print(f"  Columns: {summary['columns']}")
        print(f"  CRS: {summary['crs']}")
        print("  Dtypes:")
        for column, dtype in summary["dtypes"].items():
            print(f"    - {column}: {dtype}")
