# CDMXGNN

Project to build a spatial representation of Mexico City oriented toward recommending commercial locations through H3 hexagon integration and, afterwards, relational modeling with GNN.

For the full conceptual explanation, see [Ontology.md](/C:/Users/eduar/Desktop/CDMXGNN/Ontology.md).

## Current State

- `0_DATA/1_CLEAN` already contains verified clean layers for crime, DENUE, economic census, population census, MGE, proxies, risk, tourism, and part of SEMOVI.
- OSM currently exists only as raw road-network extraction in `0_DATA/0_RAW/OSM/drive_network`.
- Part of the pipeline has already been migrated to `.py` scripts; other legacy clean outputs still come from notebooks.

## How to Run

From PowerShell, move to the repository:

```powershell
cd C:\Users\eduar\Desktop\CDMXGNN
```

Activate the virtual environment:

```powershell
& .\.venv\Scripts\Activate.ps1
```

Then run any script with:

```powershell
python .\1_CODE\0_DATA_CLEANING\<script_path>.py
```

Examples:

```powershell
python .\1_CODE\0_DATA_CLEANING\MGE\mge_cleaning.py
python .\1_CODE\0_DATA_CLEANING\INEGI\DENUE\denue_cleaning.py
python .\1_CODE\0_DATA_CLEANING\INEGI\CENSO_ECO\censo_cleaning.py
python .\1_CODE\0_DATA_CLEANING\INEGI\CENSO_POB\censo_pob_cleaning.py
python .\1_CODE\0_DATA_CLEANING\OSM\osm_drive_network_extraction.py
```

If you do not want to activate the environment, you can use directly:

```powershell
& .\.venv\Scripts\python.exe .\1_CODE\0_DATA_CLEANING\MGE\mge_cleaning.py
```

## Current Direct Pipeline

The current reproducible `.py` entrypoints are:

1. `MGE`
```powershell
python .\1_CODE\0_DATA_CLEANING\MGE\mge_cleaning.py
```

2. `DENUE`
```powershell
python .\1_CODE\0_DATA_CLEANING\INEGI\DENUE\denue_cleaning.py
```

3. `Economic Census`
```powershell
python .\1_CODE\0_DATA_CLEANING\INEGI\CENSO_ECO\censo_cleaning.py
```

4. `Population Census`
```powershell
python .\1_CODE\0_DATA_CLEANING\INEGI\CENSO_POB\censo_pob_cleaning.py
```

5. `OSM`
```powershell
python .\1_CODE\0_DATA_CLEANING\OSM\osm_drive_network_extraction.py
```

Note: this last step only extracts the raw road network for cars and stores its tables in `0_DATA/0_RAW/OSM`. It is not yet part of `0_DATA/1_CLEAN`.

## Verified Clean Outputs

It has currently been verified that these are readable, among others:

- `CRIMEN/crime_attributes.parquet` and `CRIMEN/crime_points.parquet`
- `INEGI/DENUE/denue_clean.parquet`
- `INEGI/CENSO_ECO/censo_econ_municipio_prior.parquet`
- `INEGI/CENSO_POB/censo_pob_operativo.parquet`
- `MGE/entidad_cdmx.parquet`
- `MGE/municipios_cdmx.parquet`
- `MGE/ageb_urbana_cdmx.parquet`
- `MGE/manzanas_cdmx.parquet`
- `MGE/localidades_cdmx.parquet`
- `PROXYS/predial_aprox.parquet`
- `PROXYS/valor_suelo.parquet`
- `RIESGO_NATURAL/riesgo.parquet`
- `SEMOVI/ciclovias/ecobici.parquet`
- `SEMOVI/ciclovias/via.parquet`
- `TOURISMO/tourism.parquet`

## Note on Legacy Outputs

Not all current cleaning has already been migrated to `.py` scripts. Some outputs that are currently considered valid for the project were still generated from legacy notebooks, especially in `CRIMEN`, `PROXYS`, `RIESGO_NATURAL`, `SEMOVI`, `TOURISMO`, and `SCIAN`.
