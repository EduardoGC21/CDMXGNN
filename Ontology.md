---
fecha_creacion: 2026-04-06
type: proyecto
project: cdmx_gnn
people:
tags:
---
# Ontologia del Proyecto: CDMXGNN

Ontologia del proyecto, que se hace, por que se hace, y como se organiza conceptualmente a partir del estado actual del repositorio.

## 1. Definicion del objetivo
El proyecto busca transformar la decision de donde abrir un nuevo establecimiento en la Ciudad de Mexico desde un proceso empirico, cargado de intuicion y sesgo humano, hacia un sistema de recomendacion espacial basado en estructura urbana, actividad economica, movilidad, contexto sociodemografico y riesgo.

En la practica, el sistema no intenta responder solamente "donde hay mas negocios" o "donde vive mas gente", sino preguntas del tipo:
- que microzonas de la ciudad tienen una combinacion urbana funcionalmente atractiva para cierto giro comercial;
- que zonas se parecen estructuralmente a otras zonas exitosas, aunque no sean obvias para un analista humano;
- que zonas muestran buen contexto de accesibilidad, densidad, actividad economica y entorno urbano para soportar expansion comercial;
- que zonas parecen prometedoras por su embedding urbano, aunque sus variables aisladas no destaquen de inmediato.

La unidad espacial final del proyecto es el **hexagono H3**. Sobre esa unidad se integran las fuentes, se construye el grafo y se produce el embedding urbano.

El producto de negocio esperado es un sistema de recomendacion que entregue:
1. un **ranking Top-K de hexagonos** recomendados, condicionado al giro del negocio;
2. un **mapa interpretable** para explorar alternativas espaciales;
3. una **explicacion resumida** de por que una zona aparece como candidata, basada en densidad, accesibilidad, mezcla funcional y contexto de riesgo.

El objetivo principal del proyecto no es, por ahora, predecir revenue observado con verdad terreno propietaria, porque esos datos no existen dentro del repositorio y normalmente pertenecen al cliente. Por eso, el objetivo inmediato es aprender una **representacion urbana util para recomendacion**. Si en el futuro el cliente aporta resultados reales del negocio, los embeddings y features construidos aqui pueden servir como base para un segundo modelo de revenue, exito comercial o retorno esperado.

## 2. Datos y preparacion
### 2.1 Fuentes presentes y ya integradas en `1_CLEAN`

Las fuentes actualmente presentes y verificadas dentro del proyecto, ignorando explicitamente `DataToIntegrate`, son:
- **CRIMEN**: `crime_attributes.parquet` y `crime_points.parquet`.
- **INEGI / DENUE**: `denue_clean.parquet`.
- **INEGI / CENSO_ECO**: `censo_econ_municipio_prior.parquet`.
- **INEGI / CENSO_POB**: `censo_pob_operativo.parquet`.
- **INEGI / SCIAN**: taxonomias limpias en JSON, no en parquet.
- **MGE**: `entidad_cdmx`, `municipios_cdmx`, `ageb_urbana_cdmx`, `manzanas_cdmx`, `localidades_cdmx`.
- **PROXYS**: `predial_aprox.parquet` y `valor_suelo.parquet`.
- **RIESGO_NATURAL**: `riesgo.parquet`.
- **SEMOVI**: un estado limpio mixto; parte de la salida sigue en shapefiles por sistema y `ciclovias` ya esta en parquet.
- **TOURISMO**: `tourism.parquet`.

### 2.2 Estado actual de datos limpios

El estado actual de `0_DATA/1_CLEAN` ya no es solo scaffolding. Hoy existen artefactos limpios verificables y legibles que forman la base real del proyecto:
- `CRIMEN/crime_attributes.parquet`: `41966 x 10`, atributos del delito por registro.
- `CRIMEN/crime_points.parquet`: `41966 x 3`, capa puntual de crimen.
- `INEGI/DENUE/denue_clean.parquet`: `460762 x 18`, POIs economicos base del proyecto.
- `INEGI/CENSO_ECO/censo_econ_municipio_prior.parquet`: `20247 x 20`, priors economicos municipales por actividad.
- `INEGI/CENSO_POB/censo_pob_operativo.parquet`: `650 x 34`, poblacion y vivienda a nivel municipio-total y localidad.
- `MGE/entidad_cdmx.parquet`: `1 x 4`, poligono estatal de CDMX.
- `MGE/municipios_cdmx.parquet`: `16 x 5`, alcaldias.
- `MGE/ageb_urbana_cdmx.parquet`: `2430 x 6`, AGEBs urbanas.
- `MGE/manzanas_cdmx.parquet`: `67224 x 9`, manzanas urbanas y rurales.
- `MGE/localidades_cdmx.parquet`: `103 x 7`, localidades urbanas y rurales amanzanadas.
- `PROXYS/predial_aprox.parquet`: `1089674 x 4`, proxy territorial de predial.
- `PROXYS/valor_suelo.parquet`: `1087301 x 4`, proxy territorial de valor de suelo.
- `RIESGO_NATURAL/riesgo.parquet`: `51 x 7`, sintesis de riesgo espacial.
- `SEMOVI/ciclovias/ecobici.parquet`: `677 x 3`, estaciones o puntos asociados a ecobici.
- `SEMOVI/ciclovias/via.parquet`: `1302 x 3`, infraestructura ciclista lineal.
- `TOURISMO/tourism.parquet`: `1649 x 3`, capa puntual o espacial de actividades turisticas.

Todas estas salidas son legibles en el entorno actual. OSM todavia no aparece en `1_CLEAN`; existe solamente como extraccion de red vial cruda en `0_DATA/0_RAW/OSM/drive_network`.

### 2.3 Fuentes ya scriptificadas vs salidas legacy

El proyecto ya tiene dos tipos de preparacion:

**Limpieza en `.py` reproducible**
- `DENUE`
- `CENSO_ECO`
- `CENSO_POB`
- `MGE`
- `OSM` extraccion de red vial cruda

**Salidas limpias que todavia vienen de notebooks legacy**
- `CRIMEN`
- `PROXYS`
- `RIESGO_NATURAL`
- `SEMOVI`
- `TOURISMO`
- `SCIAN`

Esto importa porque el estado actual del repositorio ya tiene una base limpia util para avanzar a hexes y grafo, aunque no toda la preparacion haya migrado todavia al mismo nivel de reproducibilidad.

### 2.4 Convenciones de limpieza y estandarizacion

El proyecto ya muestra una logica de preparacion consistente:
- normalizacion de nombres de columnas con `unidecode`, minusculas y `_`;
- normalizacion de strings para que las categorias sean comparables;
- homologacion de CRS antes de cualquier cruce espacial;
- exportacion a `parquet` o `geoparquet` como formato canonico intermedio;
- separacion entre `0_RAW` y `1_CLEAN`.

La idea conceptual es que cada fuente quede, antes del merge por hexagono, en una forma estable:
- identificadores claros;
- columnas estandarizadas;
- geometria valida cuando aplique;
- CRS comun para las operaciones espaciales;
- semantica suficientemente limpia para poder agregarse sin ambiguedad.

### 2.5 Regla importante de alcance

`DataToIntegrate` no debe considerarse parte canonica de la arquitectura del proyecto. Puede contener experimentos, insumos auxiliares o trabajo paralelo, pero la ontologia de `CDMXGNN` se organiza solo a partir de las fuentes y salidas que viven dentro del propio repositorio.

## 3. Integracion espacial y construccion de la unidad analitica
La unidad analitica final del proyecto es una malla de **hexagonos H3**. Toda fuente debe traducirse, directa o indirectamente, a senales comparables por hexagono.

La integracion espacial no es unica para todas las fuentes; depende del tipo geometrico y de la semantica de cada capa.

### 3.1 Jerarquia espacial ahora disponible

Con la limpieza actual de MGE, el proyecto ya cuenta con una jerarquia territorial explicita:
- `entidad_cdmx`: limite estatal de CDMX, util para recortes macro y para la extraccion de OSM.
- `municipios_cdmx`: alcaldias, utiles para transferencias administrativas y priors municipales.
- `localidades_cdmx`: localidades urbanas y rurales amanzanadas, utiles para conectar `cve_loc` con el censo de poblacion.
- `ageb_urbana_cdmx`: unidad intermedia urbana para futuros agregados sociodemograficos.
- `manzanas_cdmx`: unidad fina territorial que puede servir para validacion espacial, poblacion o densidad.

Esta jerarquia vuelve mucho mas clara la futura conversion a hexagonos porque ya existe un soporte territorial interno consistente.

### 3.2 Datos puntuales
Las capas puntuales como DENUE, crimen o turismo se integran principalmente por:
- conteos por hexagono;
- conteos por categoria o subcategoria;
- posibles densidades o tasas si mas adelante se normalizan por area, poblacion o actividad.

### 3.3 Datos lineales
Las capas lineales como rutas de transporte, red vial o corredores pueden integrarse por:
- interseccion con hexagonos;
- longitud contenida o ponderada dentro del hexagono;
- conteos de lineas, segmentos o accesos segun el caso.

Aqui entra especialmente OSM, que por ahora existe como red vial cruda para automovil y todavia no como feature engineering limpio.

### 3.4 Datos poligonales
Las capas poligonales como AGEBs, municipios, localidades, manzanas, riesgo o proxys espaciales pueden integrarse por:
- interseccion con hexagonos;
- ponderacion por porcentaje de solape;
- transferencia desde municipio, localidad o AGEB hacia el hexagono cuando el dato no vive originalmente a escala puntual.

El caso de `censo_pob_operativo.parquet` es importante: la tabla ya esta limpia, pero la asignacion a hexes vendra despues, usando localidad o municipio como soporte territorial.

### 3.5 Datos agregados no espaciales a nivel fino
El caso mas importante aqui es el **Censo Economico**. Ese conjunto no describe negocios individuales, sino celdas agregadas por municipio y nivel de actividad economica. Por eso su rol no es "unirse" a DENUE registro por registro, sino aportar un **prior economico municipal** que despues puede usarse al construir features de hexagonos.

En terminos de flujo, el proyecto distingue tres momentos:
- la fuente ya limpia y lista para integrarse;
- la tabla o capa ya transformada a informacion compatible con hexagono, que conceptualmente corresponde a `0_HEX_DATA`;
- la tabla final de merge por hexagono, que conceptualmente corresponde a `1_DATA_HEX_MERGED`;
- y despues, sobre ese resultado, la construccion del grafo.

## 4. Feature engineering
El proyecto no se organiza solo por archivos, sino por **familias de senales** que intentan describir la ciudad como soporte de actividad economica y recomendacion comercial.

### 4.1 Actividad economica y funcional
DENUE y SCIAN forman la base para describir:
- presencia de establecimientos;
- competencia cercana;
- complementariedad comercial;
- mezcla sectorial o funcional del entorno.

Aqui el rol de SCIAN es fundamental porque permite decidir despues si la agregacion final conviene a nivel de sector, rama, subrama o clase, dependiendo del balance entre interpretabilidad y granularidad.

### 4.2 Priors economicos agregados
El Censo Economico entra como una capa distinta:
- no representa revenue de cada POI;
- no representa un ground truth de cada negocio;
- si representa productividad agregada por municipio y por nivel de actividad economica.

Por eso, su uso correcto es construir senales como:
- ingresos por unidad economica;
- ingresos por persona ocupada;
- produccion por unidad economica;
- personal ocupado por unidad economica.

Estas senales pueden despues enriquecer al hexagono como un prior municipal condicionado por actividad economica, usando la composicion de POIs observada en cada hexagono.

### 4.3 Poblacion y vivienda
El censo de poblacion ya no es solo una fuente conceptual. Hoy existe una tabla operativa con:
- totales de poblacion;
- poblacion femenina y masculina;
- grupos de edad agregados;
- hogares y viviendas;
- filas tanto de `municipio_total` como de `localidad`.

La utilidad inmediata de esta tabla no es el merge directo, sino preparar la futura asignacion espacial a hexes mediante localidad o municipio.

### 4.4 Movilidad y accesibilidad
SEMOVI aporta la capa de transporte publico:
- rutas;
- paradas;
- variedad modal;
- densidad o proximidad de accesibilidad.

Ademas, OSM ya existe como extraccion de red vial cruda para automovil, lista para convertirse despues en variables de conectividad y accesibilidad vial.

### 4.5 Seguridad y riesgo
Crimen y riesgo natural agregan dos dimensiones distintas:
- **seguridad**: friccion o costo esperado del entorno;
- **riesgo natural**: condicion estructural de vulnerabilidad territorial.

Estas capas no dicen si una zona es comercialmente mala por si mismas, pero si forman parte del contexto que modula deseabilidad, exposicion y robustez de una ubicacion.

### 4.6 Proxys urbanos y de valor
Las capas de proxys, como predial o valor de suelo, funcionan como una aproximacion a:
- intensidad economica del entorno;
- costo o estatus espacial;
- viabilidad o presion inmobiliaria.

No sustituyen datos privados del cliente, pero ayudan a introducir senales de valor del territorio que normalmente importan en decisiones de localizacion.

### 4.7 Contexto espacial base
MGE aporta la geometria estructural del sistema:
- red administrativa;
- localidades;
- AGEBs;
- manzanas;
- soporte cartografico para transferencias futuras.

OSM aporta la red vial cruda y mas adelante puede aportar senales de conectividad automovilistica a escala hexagonal.

### 4.8 Idea central de composicion
La mezcla sectorial especifica de cada hexagono deberia emerger principalmente de la composicion observada de POIs. En cambio, el Censo Economico debe entenderse como una capa de **intensidad economica agregada** que contextualiza esa composicion, no como una tabla de revenue por negocio.

## 5. Arquitectura espacial y construccion del grafo
La arquitectura del proyecto sigue la intuicion de que una zona urbana no se explica solo por sus atributos internos, sino por su relacion con el entorno.

### 5.1 Nodos
Cada nodo del grafo es un **hexagono H3**. El nodo contiene:
- el vector de features construido a partir del merge espacial;
- su geometria o identificador H3 como referencia espacial;
- y, eventualmente, informacion condicionada al giro comercial cuando el sistema se use como recomendador.

### 5.2 Aristas fisicas
Las aristas fisicas representan vecindad espacial. Conceptualmente pueden construirse por:
- adyacencia H3;
- vecinos mas cercanos;
- o una combinacion que garantice conectividad y contexto local.

El objetivo de estas aristas es que el embedding de un hexagono incorpore informacion de su barrio inmediato y no solo de su celda.

### 5.3 Aristas virtuales
Los documentos del capstone y el canvas tambien justifican la idea de aristas virtuales:
- unen hexagonos no necesariamente contiguos;
- se basan en similitud de features o tipologia urbana;
- amplian el campo receptivo del modelo;
- permiten conectar zonas funcionalmente parecidas aunque esten separadas fisicamente.

Esto es importante porque dos zonas pueden tener estructura comercial similar sin estar una junto a la otra.

### 5.4 Artefacto final de modelado
El resultado conceptual de esta fase es un objeto de grafo compatible con **PyTorch Geometric** o una estructura equivalente:
- nodos = hexagonos;
- aristas = relaciones fisicas y opcionalmente virtuales;
- atributos = tabla unificada de features por hexagono.

## 6. Modelado
El proyecto esta pensado como un sistema de recomendacion espacial basado en GNN, no como un clasificador de riesgo vial al estilo `MapaSinGNN`.

### 6.1 Modelo principal
La arquitectura esperada es:
- una capa inicial tipo **MLP** para armonizar y proyectar features;
- un **GNN** que aprenda embeddings urbanos de los hexagonos;
- una cabeza de score o ranking que permita ordenar zonas segun el tipo de negocio buscado.

La intuicion es que el embedding debe capturar:
- contexto local;
- estructura funcional;
- accesibilidad;
- actividad economica;
- y relaciones no triviales entre zonas.

### 6.2 Producto inmediato
El output principal no es "esta calle exacta" ni un score contable perfecto, sino una recomendacion espacial util para reducir el universo de decision a microzonas prometedoras.

Por eso el proyecto privilegia:
- ranking;
- comparacion entre candidatos;
- interpretabilidad espacial;
- embeddings utiles para exploracion.

### 6.3 Extension futura con datos privados
Si en el futuro existen datos del cliente como:
- revenue por sucursal;
- ventas;
- flujo de clientes;
- desempeno historico;

entonces el proyecto puede extenderse con un segundo modelo que use:
- features por hexagono;
- embeddings del GNN;
- y outcomes reales del negocio.

Ese segundo nivel permitiria pasar de recomendacion estructural a prediccion de revenue, exito o viabilidad economica esperada.

## 7. Evaluacion y entregable
La evaluacion del sistema debe alinearse con el problema de negocio y no solo con una metrica abstracta.

### 7.1 Evaluacion del modelo
Como la meta es recomendar zonas, la evaluacion debe enfocarse en:
- calidad del ranking;
- estabilidad de las recomendaciones;
- comparacion contra baselines no graficos;
- capacidad de encontrar zonas razonables por intuicion urbana y criterio comercial.

No basta con optimizar error promedio si el Top-K recomendado no tiene sentido operativo.

### 7.2 Comparacion con baselines
Los documentos del capstone ya contemplan comparar la GNN con modelos tradicionales. Eso es importante porque:
- obliga a justificar el valor del grafo;
- permite medir si los embeddings agregan informacion sobre un baseline tabular;
- ayuda a distinguir si la mejora viene de la arquitectura o simplemente de las features.

### 7.3 Entregable final para el usuario
El entregable esperado debe incluir:
- un ranking Top-K de hexagonos recomendados;
- un mapa interactivo o visualizacion espacial;
- una explicacion interpretable de por que ciertas zonas aparecen arriba;
- y filtros para acotar por giro, zona y restricciones operativas.

La idea no es reemplazar la validacion en campo, sino volverla mucho mas focalizada y menos intuitiva.

## 8. Que produce realmente este proyecto
En terminos practicos, este proyecto produce un sistema de representacion y recomendacion espacial con tres niveles:

1. **Representacion urbana**: convierte fuentes heterogeneas de CDMX en una base comparable por hexagono H3.
2. **Representacion relacional**: transforma esos hexagonos en un grafo donde el contexto local y la similitud urbana importan.
3. **Traduccion operativa**: convierte embeddings y scores en una lista priorizada de zonas para expansion comercial.

El resultado final no es solo una tabla con negocios o un mapa de densidad, sino una **ontologia urbana orientada a recomendacion**:
- la ciudad se vuelve un sistema de nodos comparables;
- cada nodo tiene atributos economicos, urbanos y contextuales;
- esos nodos se conectan en un grafo;
- el grafo aprende embeddings;
- y esos embeddings se traducen en decisiones de localizacion mas informadas.

En ese sentido, `CDMXGNN` no es solamente un proyecto de limpieza o de merge espacial. Es un intento de construir una capa intermedia entre la complejidad urbana de la Ciudad de Mexico y la decision concreta de donde abrir un negocio.
