from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import pandas as pd
from pandas.api.types import is_object_dtype, is_string_dtype
from unidecode import unidecode

DEFAULT_INPUT_PATH = (
    Path(__file__).resolve().parents[4]
    / "0_DATA"
    / "0_RAW"
    / "INEGI"
    / "CENSO_POB"
    / "iter_09_cpv2020"
    / "conjunto_de_datos"
    / "conjunto_de_datos_iter_09CSV20.csv"
)
DEFAULT_TAM_LOC_CATALOG_PATH = (
    Path(__file__).resolve().parents[4]
    / "0_DATA"
    / "0_RAW"
    / "INEGI"
    / "CENSO_POB"
    / "iter_09_cpv2020"
    / "catalogos"
    / "tam_loc.csv.csv"
)
DEFAULT_OUTPUT_PATH = (
    Path(__file__).resolve().parents[4]
    / "0_DATA"
    / "1_CLEAN"
    / "INEGI"
    / "CENSO_POB"
    / "censo_pob_operativo.parquet"
)


def read_csv_with_fallback(path: str | Path) -> pd.DataFrame:
    for encoding in ["utf-8", "utf-8-sig", "cp1252", "latin1"]:
        try:
            return pd.read_csv(path, encoding=encoding)
        except UnicodeDecodeError:
            continue
    raise UnicodeDecodeError("unknown", b"", 0, 1, f"Could not decode CSV file: {path}")


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
    target_columns = include_columns if include_columns is not None else list(df.columns)
    for column in df.columns:
        if column not in target_columns:
            continue
        if not (is_string_dtype(df[column]) or is_object_dtype(df[column])):
            continue
        df[column] = df[column].map(standardize_string)
    return df


def format_code(value: Any, width: int) -> str | pd.NA:
    if pd.isna(value):
        return pd.NA

    text = str(value).strip()
    if not text:
        return pd.NA

    match = re.fullmatch(r"\d+(?:\.0+)?", text)
    if not match:
        return pd.NA

    return str(int(float(text))).zfill(width)


def replace_placeholder_markers(df: pd.DataFrame) -> pd.DataFrame:
    return df.replace({"*": pd.NA, "nan": pd.NA, "": pd.NA})


def numeric_or_na(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce")


def sum_columns(df: pd.DataFrame, columns: list[str]) -> pd.Series:
    numeric = df.loc[:, columns].apply(numeric_or_na)
    return numeric.sum(axis=1, min_count=1)


def load_tam_loc_catalog(catalog_path: str | Path) -> pd.DataFrame:
    catalog = read_csv_with_fallback(catalog_path)
    catalog = standardize_columns(catalog)
    catalog = replace_placeholder_markers(catalog)
    catalog["tam_loc"] = catalog["tam_loc"].map(lambda value: format_code(value, width=2))
    catalog["tam_loc_descripcion"] = catalog["descripcion"].map(standardize_string)
    return catalog.loc[:, ["tam_loc", "tam_loc_descripcion"]]


def _prepare_base_population(input_path: str | Path) -> tuple[pd.DataFrame, int]:
    population = read_csv_with_fallback(input_path)
    rows_before_filter = len(population)
    population = standardize_columns(population)
    population = replace_placeholder_markers(population)
    population = standardize_string_values(
        population,
        include_columns=["nom_ent", "nom_mun", "nom_loc"],
    )

    population = population.assign(
        cve_ent=population["entidad"].map(lambda value: format_code(value, width=2)),
        cve_mun=population["mun"].map(lambda value: format_code(value, width=3)),
        cve_loc=population["loc"].map(lambda value: format_code(value, width=4)),
    )

    population = population.loc[population["cve_ent"] == "09"].copy()
    population["row_type"] = pd.NA
    population.loc[population["cve_loc"] == "0000", "row_type"] = "municipio_total"
    population.loc[
        population["cve_loc"].notna() & ~population["cve_loc"].isin(["0000", "9998", "9999"]),
        "row_type",
    ] = "localidad"

    population = population.loc[population["row_type"].notna()].copy()
    population = population.loc[population["cve_mun"] != "000"].copy()
    population = population.loc[~population["cve_loc"].isin(["9998", "9999"])].copy()

    population["has_coordinates_flag"] = population["longitud"].notna() & population["latitud"].notna()
    return population, rows_before_filter


def add_age_bins(df: pd.DataFrame) -> pd.DataFrame:
    df["poblacion_0_9_f"] = sum_columns(df, ["p_0a4_f", "p_5a9_f"])
    df["poblacion_0_9_m"] = sum_columns(df, ["p_0a4_m", "p_5a9_m"])
    df["poblacion_10_19_f"] = sum_columns(df, ["p_10a14_f", "p_15a19_f"])
    df["poblacion_10_19_m"] = sum_columns(df, ["p_10a14_m", "p_15a19_m"])
    df["poblacion_20_29_f"] = sum_columns(df, ["p_20a24_f", "p_25a29_f"])
    df["poblacion_20_29_m"] = sum_columns(df, ["p_20a24_m", "p_25a29_m"])
    df["poblacion_30_39_f"] = sum_columns(df, ["p_30a34_f", "p_35a39_f"])
    df["poblacion_30_39_m"] = sum_columns(df, ["p_30a34_m", "p_35a39_m"])
    df["poblacion_40_49_f"] = sum_columns(df, ["p_40a44_f", "p_45a49_f"])
    df["poblacion_40_49_m"] = sum_columns(df, ["p_40a44_m", "p_45a49_m"])
    df["poblacion_50_59_f"] = sum_columns(df, ["p_50a54_f", "p_55a59_f"])
    df["poblacion_50_59_m"] = sum_columns(df, ["p_50a54_m", "p_55a59_m"])
    df["poblacion_60_y_mas_f"] = sum_columns(
        df,
        ["p_60a64_f", "p_65a69_f", "p_70a74_f", "p_75a79_f", "p_80a84_f", "p_85ymas_f"],
    )
    df["poblacion_60_y_mas_m"] = sum_columns(
        df,
        ["p_60a64_m", "p_65a69_m", "p_70a74_m", "p_75a79_m", "p_80a84_m", "p_85ymas_m"],
    )
    return df


def add_validation_flags(df: pd.DataFrame) -> pd.DataFrame:
    female = numeric_or_na(df["poblacion_femenina"])
    male = numeric_or_na(df["poblacion_masculina"])
    total = numeric_or_na(df["poblacion_total"])

    df["population_total_mismatch_flag"] = (
        female.notna()
        & male.notna()
        & total.notna()
        & ((female + male) != total)
    )
    return df


def rename_compact_columns(df: pd.DataFrame) -> pd.DataFrame:
    return df.rename(
        columns={
            "nom_ent": "nom_ent",
            "nom_mun": "nom_mun",
            "nom_loc": "nom_loc",
            "pobtot": "poblacion_total",
            "pobfem": "poblacion_femenina",
            "pobmas": "poblacion_masculina",
            "rel_h_m": "relacion_hombres_mujeres",
            "tothog": "total_hogares",
            "vivtot": "total_viviendas",
            "tvivhab": "total_viviendas_habitadas",
        }
    )


def select_output_columns(df: pd.DataFrame) -> pd.DataFrame:
    output_columns = [
        "cve_ent",
        "nom_ent",
        "cve_mun",
        "nom_mun",
        "cve_loc",
        "nom_loc",
        "row_type",
        "longitud",
        "latitud",
        "has_coordinates_flag",
        "tam_loc",
        "tam_loc_descripcion",
        "poblacion_total",
        "poblacion_femenina",
        "poblacion_masculina",
        "relacion_hombres_mujeres",
        "poblacion_0_9_f",
        "poblacion_0_9_m",
        "poblacion_10_19_f",
        "poblacion_10_19_m",
        "poblacion_20_29_f",
        "poblacion_20_29_m",
        "poblacion_30_39_f",
        "poblacion_30_39_m",
        "poblacion_40_49_f",
        "poblacion_40_49_m",
        "poblacion_50_59_f",
        "poblacion_50_59_m",
        "poblacion_60_y_mas_f",
        "poblacion_60_y_mas_m",
        "total_hogares",
        "total_viviendas",
        "total_viviendas_habitadas",
        "population_total_mismatch_flag",
    ]
    return df.loc[:, output_columns].sort_values(
        by=["row_type", "cve_mun", "cve_loc"],
        kind="stable",
    ).reset_index(drop=True)


def _build_summary(rows_before_filter: int, output_df: pd.DataFrame, output_path: Path) -> dict[str, Any]:
    return {
        "rows_before_filter": rows_before_filter,
        "rows_after_filter": len(output_df),
        "row_type_counts": output_df["row_type"].value_counts().sort_index().to_dict(),
        "municipio_total_rows": int((output_df["row_type"] == "municipio_total").sum()),
        "localidad_rows": int((output_df["row_type"] == "localidad").sum()),
        "rows_with_coordinates": int(output_df["has_coordinates_flag"].sum()),
        "population_total_mismatch_rows": int(output_df["population_total_mismatch_flag"].sum()),
        "output_path": str(output_path),
    }


def clean_censo_pob(
    input_path: str | Path = DEFAULT_INPUT_PATH,
    tam_loc_catalog_path: str | Path = DEFAULT_TAM_LOC_CATALOG_PATH,
    output_path: str | Path = DEFAULT_OUTPUT_PATH,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    input_path = Path(input_path)
    tam_loc_catalog_path = Path(tam_loc_catalog_path)
    output_path = Path(output_path)

    population, rows_before_filter = _prepare_base_population(input_path)
    tam_loc_catalog = load_tam_loc_catalog(tam_loc_catalog_path)

    population["tam_loc"] = population["tamloc"].map(lambda value: format_code(value, width=2))
    population = population.merge(tam_loc_catalog, on="tam_loc", how="left")

    population = rename_compact_columns(population)

    numeric_columns = [
        "poblacion_total",
        "poblacion_femenina",
        "poblacion_masculina",
        "relacion_hombres_mujeres",
        "total_hogares",
        "total_viviendas",
        "total_viviendas_habitadas",
    ]
    for column in numeric_columns:
        population[column] = numeric_or_na(population[column])

    population = add_age_bins(population)
    population = add_validation_flags(population)
    output_df = select_output_columns(population)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_df.to_parquet(output_path, index=False)

    summary = _build_summary(rows_before_filter=rows_before_filter, output_df=output_df, output_path=output_path)
    return output_df, summary


if __name__ == "__main__":
    censo_pob_df, summary = clean_censo_pob()
    print(f"Saved {summary['rows_after_filter']:,} population rows to {summary['output_path']}")
    print(f"Input rows: {summary['rows_before_filter']:,}")
    print("Counts by row_type:")
    for row_type, count in summary["row_type_counts"].items():
        print(f"  - {row_type}: {count:,}")
    print(f"Municipio total rows: {summary['municipio_total_rows']:,}")
    print(f"Localidad rows: {summary['localidad_rows']:,}")
    print(f"Rows with coordinates: {summary['rows_with_coordinates']:,}")
    print(f"Population total mismatch rows: {summary['population_total_mismatch_rows']:,}")
    print("Schema:")
    for column in censo_pob_df.columns:
        print(f"  - {column}")
    print("Preview:")
    print(censo_pob_df.head())
