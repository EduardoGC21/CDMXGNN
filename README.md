# CDMXGNN

Proyecto para construir una representacion espacial de la Ciudad de Mexico orientada a recomendacion de ubicaciones comerciales mediante integracion por hexagono H3 y, despues, modelado relacional con GNN.

Para la explicacion conceptual completa, revisar [Ontology.md](/C:/Users/eduar/Desktop/CDMXGNN/Ontology.md).

## Estado actual

- `0_DATA/1_CLEAN` ya contiene capas limpias verificadas para crimen, DENUE, censo economico, censo de poblacion, MGE, proxys, riesgo, turismo y parte de SEMOVI.
- OSM existe por ahora solo como extraccion cruda de red vial en `0_DATA/0_RAW/OSM/drive_network`.
- Parte del pipeline ya esta migrada a scripts `.py`; otras salidas limpias legacy todavia provienen de notebooks.

## Como correr

Desde PowerShell, ubicarse en el repositorio:

```powershell
cd C:\Users\eduar\Desktop\CDMXGNN
```

Activar el entorno virtual:

```powershell
& .\.venv\Scripts\Activate.ps1
```

Despues correr cualquier script con:

```powershell
python .\1_CODE\0_DATA_CLEANING\<ruta_del_script>.py
```

Ejemplos:

```powershell
python .\1_CODE\0_DATA_CLEANING\MGE\mge_cleaning.py
python .\1_CODE\0_DATA_CLEANING\INEGI\DENUE\denue_cleaning.py
python .\1_CODE\0_DATA_CLEANING\INEGI\CENSO_ECO\censo_cleaning.py
python .\1_CODE\0_DATA_CLEANING\INEGI\CENSO_POB\censo_pob_cleaning.py
python .\1_CODE\0_DATA_CLEANING\OSM\osm_drive_network_extraction.py
```

Si no quieres activar el entorno, puedes usar directamente:

```powershell
& .\.venv\Scripts\python.exe .\1_CODE\0_DATA_CLEANING\MGE\mge_cleaning.py
```

## Pipeline directo actual

Los entrypoints reproducibles actuales en `.py` son:

1. `MGE`
```powershell
python .\1_CODE\0_DATA_CLEANING\MGE\mge_cleaning.py
```

2. `DENUE`
```powershell
python .\1_CODE\0_DATA_CLEANING\INEGI\DENUE\denue_cleaning.py
```

3. `Censo Economico`
```powershell
python .\1_CODE\0_DATA_CLEANING\INEGI\CENSO_ECO\censo_cleaning.py
```

4. `Censo de Poblacion`
```powershell
python .\1_CODE\0_DATA_CLEANING\INEGI\CENSO_POB\censo_pob_cleaning.py
```

5. `OSM`
```powershell
python .\1_CODE\0_DATA_CLEANING\OSM\osm_drive_network_extraction.py
```

Nota: este ultimo paso solo extrae la red vial cruda para automovil y guarda sus tablas en `0_DATA/0_RAW/OSM`. Todavia no forma parte de `0_DATA/1_CLEAN`.


## Datos Que Alimentan El Grafo

Las capas actualmente consideradas para la construccion del grafo y del merge final por hexagono son:

### Capas economicas y de actividad
- `INEGI/DENUE/denue_clean.parquet`
- `INEGI/CENSO_ECO/censo_econ_municipio_prior.parquet`
- `TOURISMO/tourism.parquet`

### Capas sociodemograficas
- `INEGI/CENSO_POB/censo_pob_operativo.parquet`

### Capas territoriales base
- `MGE/entidad_cdmx.parquet`
- `MGE/municipios_cdmx.parquet`
- `MGE/ageb_urbana_cdmx.parquet`
- `MGE/manzanas_cdmx.parquet`
- `MGE/localidades_cdmx.parquet`

### Capas de seguridad y riesgo
- `CRIMEN/crime_attributes.parquet`
- `CRIMEN/crime_points.parquet`
- `RIESGO_NATURAL/riesgo.parquet`

### Proxys urbanos y de valor
- `PROXYS/predial_aprox.parquet`
- `PROXYS/valor_suelo.parquet`

### Movilidad y conectividad
- `SEMOVI/ciclovias/ecobici.parquet`
- `SEMOVI/ciclovias/via.parquet`
- `OSM`
  - actualmente en extraccion cruda de red vial
  - se usara para features de conectividad automovilistica antes del merge final a hexagonos

## Nota
No todas las capas entran al grafo de la misma forma:
- algunas se agregan por conteo de puntos por hexagono;
- otras se transfieren por interseccion espacial o porcentaje de solape;
- y otras funcionan como priors agregados a nivel municipio o localidad.
