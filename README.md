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

