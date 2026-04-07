from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import geopandas as gpd
import pandas as pd
from pandas.api.types import is_object_dtype, is_string_dtype
from pyproj import CRS
from unidecode import unidecode

TARGET_CRS = "EPSG:6372"
DROP_COLUMNS = {
    "tipo_vial",
    "nom_vial",
    "tipo_v_e_1",
    "nom_v_e_1",
    "tipo_v_e_2",
    "nom_v_e_2",
    "tipo_v_e_3",
    "nom_v_e_3",
    "numero_ext",
    "letra_ext",
    "edificio",
    "edificio_e",
    "numero_int",
    "letra_int",
    "tipo_asent",
    "nomb_asent",
    "tipocencom",
    "nom_cencom",
    "num_local",
    "cod_postal",
    "telefono",
    "correoelec",
    "www",
    "fecha_alta",
    "raz_social",
}
PER_OCU_TO_ID_ESTRATO = {
    "0_a_5_personas": "1",
    "6_a_10_personas": "1",
    "11_a_30_personas": "2",
    "31_a_50_personas": "2",
    "51_a_100_personas": "3",
    "101_a_250_personas": "3",
    "251_y_mas_personas": "4",
}

DEFAULT_INPUT_PATH = (
    Path(__file__).resolve().parents[4]
    / "0_DATA"
    / "0_RAW"
    / "INEGI"
    / "DENUE"
    / "conjunto_de_datos"
    / "denue_inegi_09_.shp"
)
DEFAULT_OUTPUT_PATH = (
    Path(__file__).resolve().parents[4]
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


def standardize_string_values(df: pd.DataFrame) -> pd.DataFrame:
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
        df[column] = df[column].map(standardize_string)
    return df


def _validate_raw_crs(gdf: gpd.GeoDataFrame) -> CRS:
    if gdf.crs is None:
        raise ValueError("DENUE source geometry has no CRS.")

    source_crs = CRS.from_user_input(gdf.crs)
    if not source_crs.is_geographic:
        raise ValueError(f"Expected geographic DENUE source CRS, got {source_crs.to_string()}.")
    return source_crs


def _build_summary(
    source_crs: CRS,
    target_crs: CRS,
    rows_before_filter: int,
    rows_after_filter: int,
    dropped_columns: list[str],
    output_path: Path,
) -> dict[str, Any]:
    return {
        "source_crs": source_crs.to_string(),
        "target_crs": target_crs.to_string(),
        "rows_before_filter": rows_before_filter,
        "rows_after_filter": rows_after_filter,
        "rows_removed_non_cdmx": rows_before_filter - rows_after_filter,
        "dropped_columns": dropped_columns,
        "output_path": str(output_path),
    }


def add_id_estrato_from_per_ocu(df: pd.DataFrame) -> pd.DataFrame:
    if "per_ocu" not in df.columns:
        return df

    df["id_estrato"] = df["per_ocu"].map(PER_OCU_TO_ID_ESTRATO)
    df = df.drop(columns=["per_ocu"])
    return df


def clean_denue(
    input_path: str | Path = DEFAULT_INPUT_PATH,
    output_path: str | Path = DEFAULT_OUTPUT_PATH,
    target_crs: str | int = TARGET_CRS,
) -> tuple[gpd.GeoDataFrame, dict[str, Any]]:
    input_path = Path(input_path)
    output_path = Path(output_path)

    gdf = gpd.read_file(input_path)
    source_crs = _validate_raw_crs(gdf)

    gdf = standardize_columns(gdf)

    if "cve_ent" not in gdf.columns:
        raise KeyError("Expected 'cve_ent' column after normalization.")

    rows_before_filter = len(gdf)
    gdf = standardize_string_values(gdf)
    gdf = gdf.loc[gdf["cve_ent"] == "09"].copy()
    rows_after_filter = len(gdf)
    gdf = add_id_estrato_from_per_ocu(gdf)

    dropped_columns = sorted(DROP_COLUMNS.intersection(gdf.columns))
    gdf = gdf.drop(columns=dropped_columns)

    target_crs_obj = CRS.from_user_input(target_crs)
    gdf = gdf.to_crs(target_crs_obj)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    gdf.to_parquet(output_path)

    summary = _build_summary(
        source_crs=source_crs,
        target_crs=target_crs_obj,
        rows_before_filter=rows_before_filter,
        rows_after_filter=rows_after_filter,
        dropped_columns=dropped_columns,
        output_path=output_path,
    )
    return gdf, summary


if __name__ == "__main__":
    denue_gdf, validation = clean_denue()
    print(f"Saved {len(denue_gdf):,} DENUE rows to {validation['output_path']}")
    print(f"Source CRS: {validation['source_crs']}")
    print(f"Target CRS: {validation['target_crs']}")
    print(f"Removed non-CDMX rows: {validation['rows_removed_non_cdmx']:,}")
    print(f"Columns: {len(denue_gdf.columns)}")
    print("Schema:")
    for column in denue_gdf.columns:
        print(f"  - {column}")
    print("Preview:")
    print(denue_gdf.head())
