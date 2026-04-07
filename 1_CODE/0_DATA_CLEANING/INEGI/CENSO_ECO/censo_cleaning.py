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
    / "CENSO_ECO"
    / "conjunto_de_datos"
    / "tr_ce_cdmx_2024.csv"
)
DEFAULT_MUNICIPIO_CATALOG_PATH = (
    Path(__file__).resolve().parents[4]
    / "0_DATA"
    / "0_RAW"
    / "INEGI"
    / "CENSO_ECO"
    / "catalogos"
    / "tc_entidad_municipio.csv"
)
DEFAULT_OUTPUT_PATH = (
    Path(__file__).resolve().parents[4]
    / "0_DATA"
    / "1_CLEAN"
    / "INEGI"
    / "CENSO_ECO"
    / "censo_econ_municipio_prior.parquet"
)
RAW_RENAME_MAP = {
    "ue": "unidades_economicas",
    "h001a": "personal_ocupado_total",
    "a111a": "produccion_bruta_total_millones_pesos",
    "m000a": "ingresos_por_suministro_de_bienes_y_servicios_millones_pesos",
    "a800a": "total_de_ingresos_millones_pesos",
}
DERIVED_RENAME_MAP = {
    "revenue_per_ue": "total_de_ingresos_por_unidad_economica",
    "income_per_ue": "ingresos_por_suministro_por_unidad_economica",
    "production_per_ue": "produccion_bruta_total_por_unidad_economica",
    "workers_per_ue": "personal_ocupado_total_por_unidad_economica",
    "revenue_per_worker": "total_de_ingresos_por_persona_ocupada",
}
DERIVED_VALUE_COLUMNS = [
    "total_de_ingresos_por_unidad_economica",
    "ingresos_por_suministro_por_unidad_economica",
    "produccion_bruta_total_por_unidad_economica",
    "personal_ocupado_total_por_unidad_economica",
    "total_de_ingresos_por_persona_ocupada",
]
LEVEL_CODE_COLUMNS = ["sector", "rama", "subrama"]
LEVEL_LENGTHS = {"sector": 2, "rama": 4, "subrama": 5}
SIZE_BIN_MAP = {
    "1": "small",
    "2": "medium",
    "3": "medium",
    "4": "large",
    "99": "confidential",
}


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


def standardize_string_values(df: pd.DataFrame) -> pd.DataFrame:
    for column in df.columns:
        if not (is_string_dtype(df[column]) or is_object_dtype(df[column])):
            continue
        df[column] = df[column].map(standardize_string)
    return df


def format_code(value: Any, width: int | None = None) -> str | pd.NA:
    if pd.isna(value):
        return pd.NA

    text = str(value).strip()
    if not text:
        return pd.NA

    numeric_match = re.fullmatch(r"\d+(?:\.0+)?", text)
    if numeric_match:
        text = str(int(float(text)))
    else:
        text = standardize_string(text)

    if width is not None and text.isdigit():
        text = text.zfill(width)
    return text


def safe_divide(numerator: pd.Series, denominator: pd.Series) -> pd.Series:
    result = numerator / denominator
    return result.mask(denominator.isna() | numerator.isna() | (denominator == 0))


def load_municipio_catalog(catalog_path: str | Path) -> pd.DataFrame:
    catalog = read_csv_with_fallback(catalog_path)
    catalog = standardize_columns(catalog)
    catalog["cve_ent"] = catalog["e03"].map(lambda value: format_code(value, width=2))
    catalog["cve_mun"] = catalog["e04"].map(lambda value: format_code(value, width=3))
    catalog["municipio"] = catalog["nom_mun"].map(standardize_string)
    catalog = catalog.loc[catalog["cve_ent"] == "09", ["cve_ent", "cve_mun", "municipio"]].copy()
    return catalog.drop_duplicates(subset=["cve_ent", "cve_mun"])


def _prepare_base_censo(input_path: str | Path) -> tuple[pd.DataFrame, int]:
    censo = read_csv_with_fallback(input_path)
    rows_before_filter = len(censo)
    censo = standardize_columns(censo)

    censo["cve_ent"] = censo["e03"].map(lambda value: format_code(value, width=2))
    censo["cve_mun"] = censo["e04"].map(lambda value: format_code(value, width=3))
    censo["sector"] = censo["sector"].map(lambda value: format_code(value, width=2))
    censo["rama"] = censo["rama"].map(lambda value: format_code(value, width=4))
    censo["subrama"] = censo["subrama"].map(lambda value: format_code(value, width=5))
    censo["codigo"] = censo["codigo"].map(format_code)
    censo["id_estrato_raw"] = censo["id_estrato"].map(format_code)

    censo = standardize_string_values(censo)
    censo = censo.loc[(censo["cve_ent"] == "09") & censo["cve_mun"].notna()].copy()
    return censo, rows_before_filter


def _build_level_frame(censo: pd.DataFrame, level_type: str) -> pd.DataFrame:
    level_column = level_type
    length = LEVEL_LENGTHS[level_type]

    level_df = censo.loc[censo[level_column].notna()].copy()
    level_df = level_df.loc[level_df["codigo"].notna() & level_df["codigo"].str.isdigit()].copy()
    level_df = level_df.loc[level_df["codigo"].str.len() == length].copy()

    level_df["level_type"] = level_type
    level_df["size_bin"] = level_df["id_estrato_raw"].map(SIZE_BIN_MAP).fillna("all")
    return level_df


def _select_output_columns(df: pd.DataFrame) -> pd.DataFrame:
    output_columns = [
        "cve_ent",
        "cve_mun",
        "municipio",
        "level_type",
        "codigo",
        "sector",
        "rama",
        "subrama",
        "id_estrato_raw",
        "size_bin",
        "ue",
        "h001a",
        "a111a",
        "m000a",
        "a800a",
        "revenue_per_ue",
        "income_per_ue",
        "production_per_ue",
        "workers_per_ue",
        "revenue_per_worker",
    ]
    output_df = df.loc[:, output_columns].rename(columns={**RAW_RENAME_MAP, **DERIVED_RENAME_MAP})
    return output_df.sort_values(
        by=["cve_mun", "level_type", "codigo", "id_estrato_raw"],
        na_position="first",
    ).reset_index(drop=True)


def _build_summary(
    rows_before_filter: int,
    output_df: pd.DataFrame,
    output_path: Path,
) -> dict[str, Any]:
    level_counts = output_df["level_type"].value_counts().sort_index().to_dict()
    size_bin_counts = output_df["size_bin"].value_counts().sort_index().to_dict()
    null_rates = output_df[DERIVED_VALUE_COLUMNS].isna().mean().round(4).to_dict()

    return {
        "rows_before_filter": rows_before_filter,
        "rows_after_filter": len(output_df),
        "level_counts": level_counts,
        "size_bin_counts": size_bin_counts,
        "null_rates": null_rates,
        "output_path": str(output_path),
    }


def build_rama_municipio_summary(output_df: pd.DataFrame) -> pd.DataFrame:
    rama_all = output_df.loc[
        (output_df["level_type"] == "rama") & (output_df["size_bin"] == "all")
    ].copy()

    summary = (
        rama_all.groupby(["cve_mun", "municipio"], dropna=False)
        .agg(
            ramas=("codigo", "count"),
            ramas_with_revenue=("total_de_ingresos_millones_pesos", lambda series: int(series.notna().sum())),
            ramas_with_workers=("personal_ocupado_total", lambda series: int(series.notna().sum())),
            unidades_economicas_totales=("unidades_economicas", "sum"),
            total_de_ingresos_millones_pesos=("total_de_ingresos_millones_pesos", "sum"),
            ingresos_por_suministro_millones_pesos=(
                "ingresos_por_suministro_de_bienes_y_servicios_millones_pesos",
                "sum",
            ),
            produccion_bruta_total_millones_pesos=("produccion_bruta_total_millones_pesos", "sum"),
            personal_ocupado_total=("personal_ocupado_total", "sum"),
        )
        .reset_index()
        .sort_values("cve_mun")
        .reset_index(drop=True)
    )

    summary["total_de_ingresos_por_unidad_economica"] = safe_divide(
        summary["total_de_ingresos_millones_pesos"], summary["unidades_economicas_totales"]
    )
    summary["total_de_ingresos_por_persona_ocupada"] = safe_divide(
        summary["total_de_ingresos_millones_pesos"], summary["personal_ocupado_total"]
    )
    return summary


def clean_enrich_censo(
    input_path: str | Path = DEFAULT_INPUT_PATH,
    municipio_catalog_path: str | Path = DEFAULT_MUNICIPIO_CATALOG_PATH,
    output_path: str | Path = DEFAULT_OUTPUT_PATH,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    input_path = Path(input_path)
    municipio_catalog_path = Path(municipio_catalog_path)
    output_path = Path(output_path)

    censo, rows_before_filter = _prepare_base_censo(input_path)
    municipios = load_municipio_catalog(municipio_catalog_path)

    censo = censo.merge(municipios, on=["cve_ent", "cve_mun"], how="left")

    level_frames = [_build_level_frame(censo, level_type) for level_type in ["sector", "rama", "subrama"]]
    output_df = pd.concat(level_frames, ignore_index=True)

    output_df["revenue_per_ue"] = safe_divide(output_df["a800a"], output_df["ue"])
    output_df["income_per_ue"] = safe_divide(output_df["m000a"], output_df["ue"])
    output_df["production_per_ue"] = safe_divide(output_df["a111a"], output_df["ue"])
    output_df["workers_per_ue"] = safe_divide(output_df["h001a"], output_df["ue"])
    output_df["revenue_per_worker"] = safe_divide(output_df["a800a"], output_df["h001a"])

    output_df = _select_output_columns(output_df)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_df.to_parquet(output_path, index=False)

    summary = _build_summary(rows_before_filter=rows_before_filter, output_df=output_df, output_path=output_path)
    return output_df, summary


if __name__ == "__main__":
    censo_df, summary = clean_enrich_censo()
    rama_summary = build_rama_municipio_summary(censo_df)
    print(f"Saved {summary['rows_after_filter']:,} censo rows to {summary['output_path']}")
    print(f"Input rows: {summary['rows_before_filter']:,}")
    print("Counts by level_type:")
    for level_type, count in summary["level_counts"].items():
        print(f"  - {level_type}: {count:,}")
    print("Counts by size_bin:")
    for size_bin, count in summary["size_bin_counts"].items():
        print(f"  - {size_bin}: {count:,}")
    print("Null rates for derived metrics:")
    for column, null_rate in summary["null_rates"].items():
        print(f"  - {column}: {null_rate:.2%}")
    print("Schema:")
    for column in censo_df.columns:
        print(f"  - {column}")
    print("Preview:")
    print(censo_df.head())
    print("Rama-level municipio summary (size_bin=all):")
    print(rama_summary.to_string(index=False))
