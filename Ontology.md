---
fecha_creacion: 2026-04-06
type: proyecto
project: cdmx_gnn
people:
tags:
---
# Project Ontology: CDMXGNN

Project ontology: what it does, why it exists, and how it is conceptually organized based on the current state of the repository.

## 1. Objective Definition
The project seeks to transform the decision of where to open a new establishment in Mexico City from an empirical process, loaded with intuition and human bias, into a spatial recommendation system based on urban structure, economic activity, mobility, sociodemographic context, and risk.

In practice, the system does not try to answer only "where there are more businesses" or "where more people live," but questions such as:
- which micro-zones of the city have a functionally attractive urban combination for a certain business type;
- which zones are structurally similar to other successful zones, even if they are not obvious to a human analyst;
- which zones show a good context of accessibility, density, economic activity, and urban environment to support commercial expansion;
- which zones seem promising because of their urban embedding, even if their isolated variables do not stand out immediately.

The final spatial unit of the project is the **H3 hexagon**. On that unit, sources are integrated, the graph is built, and the urban embedding is produced.

The expected business product is a recommendation system that delivers:
1. a **Top-K ranking of recommended hexagons**, conditioned on business type;
2. an **interpretable map** to explore spatial alternatives;
3. a **short explanation** of why an area appears as a candidate, based on density, accessibility, functional mix, and risk context.

The main objective of the project is not, for now, to predict observed revenue with proprietary ground truth, because that data does not exist inside the repository and normally belongs to the client. For that reason, the immediate objective is to learn an **urban representation useful for recommendation**. If in the future the client provides real business outcomes, the embeddings and features built here can serve as the basis for a second model for revenue, commercial success, or expected return.

## 2. Data and Preparation
### 2.1 Sources present and already integrated in `1_CLEAN`

The sources currently present and verified inside the project, explicitly ignoring `DataToIntegrate`, are:
- **CRIMEN**: `crime_attributes.parquet` and `crime_points.parquet`.
- **INEGI / DENUE**: `denue_clean.parquet`.
- **INEGI / CENSO_ECO**: `censo_econ_municipio_prior.parquet`.
- **INEGI / CENSO_POB**: `censo_pob_operativo.parquet`.
- **INEGI / SCIAN**: cleaned taxonomies in JSON, not parquet.
- **MGE**: `entidad_cdmx`, `municipios_cdmx`, `ageb_urbana_cdmx`, `manzanas_cdmx`, `localidades_cdmx`.
- **PROXYS**: `predial_aprox.parquet` and `valor_suelo.parquet`.
- **RIESGO_NATURAL**: `riesgo.parquet`.
- **SEMOVI**: a mixed clean state; part of the output still remains in shapefiles by system and `ciclovias` is already in parquet.
- **TOURISMO**: `tourism.parquet`.

### 2.2 Current state of cleaned data

The current state of `0_DATA/1_CLEAN` is no longer just scaffolding. There are now verifiable and readable clean artifacts that form the real base of the project:
- `CRIMEN/crime_attributes.parquet`: `41966 x 10`, crime attributes by record.
- `CRIMEN/crime_points.parquet`: `41966 x 3`, point crime layer.
- `INEGI/DENUE/denue_clean.parquet`: `460762 x 18`, economic POIs that serve as the project base.
- `INEGI/CENSO_ECO/censo_econ_municipio_prior.parquet`: `20247 x 20`, municipal economic priors by activity.
- `INEGI/CENSO_POB/censo_pob_operativo.parquet`: `650 x 34`, population and housing at municipality-total and locality level.
- `MGE/entidad_cdmx.parquet`: `1 x 4`, state polygon of CDMX.
- `MGE/municipios_cdmx.parquet`: `16 x 5`, boroughs.
- `MGE/ageb_urbana_cdmx.parquet`: `2430 x 6`, urban AGEBs.
- `MGE/manzanas_cdmx.parquet`: `67224 x 9`, urban and rural blocks.
- `MGE/localidades_cdmx.parquet`: `103 x 7`, urban and rural built localities.
- `PROXYS/predial_aprox.parquet`: `1089674 x 4`, territorial property-tax proxy.
- `PROXYS/valor_suelo.parquet`: `1087301 x 4`, territorial land-value proxy.
- `RIESGO_NATURAL/riesgo.parquet`: `51 x 7`, spatial risk summary.
- `SEMOVI/ciclovias/ecobici.parquet`: `677 x 3`, stations or points associated with ecobici.
- `SEMOVI/ciclovias/via.parquet`: `1302 x 3`, linear cycling infrastructure.
- `TOURISMO/tourism.parquet`: `1649 x 3`, point or spatial layer of tourism activities.

All of these outputs are readable in the current environment. OSM still does not appear in `1_CLEAN`; it exists only as raw road-network extraction in `0_DATA/0_RAW/OSM/drive_network`.

### 2.3 Sources already scripted vs legacy outputs

The project already has two types of preparation:

**Reproducible `.py` cleaning**
- `DENUE`
- `CENSO_ECO`
- `CENSO_POB`
- `MGE`
- `OSM` raw road-network extraction

**Clean outputs that still come from legacy notebooks**
- `CRIMEN`
- `PROXYS`
- `RIESGO_NATURAL`
- `SEMOVI`
- `TOURISMO`
- `SCIAN`

This matters because the current state of the repository already has a clean base useful to move forward to hexes and graph construction, even though not all preparation has yet been migrated to the same level of reproducibility.

### 2.4 Cleaning and standardization conventions

The project already shows a consistent preparation logic:
- column-name normalization with `unidecode`, lowercase, and `_`;
- string normalization so categories are comparable;
- CRS harmonization before any spatial join;
- export to `parquet` or `geoparquet` as the canonical intermediate format;
- separation between `0_RAW` and `1_CLEAN`.

The conceptual idea is that each source should be, before the hexagon merge, in a stable form:
- clear identifiers;
- standardized columns;
- valid geometry when applicable;
- common CRS for spatial operations;
- semantics clean enough to be aggregated without ambiguity.

### 2.5 Important scope rule

`DataToIntegrate` should not be considered a canonical part of the project architecture. It may contain experiments, auxiliary inputs, or parallel work, but the ontology of `CDMXGNN` is organized only from sources and outputs that live inside the repository itself.

## 3. Spatial Integration and Construction of the Analytical Unit
The final analytical unit of the project is a grid of **H3 hexagons**. Every source must be translated, directly or indirectly, into signals comparable by hexagon.

Spatial integration is not the same for all sources; it depends on the geometry type and the semantics of each layer.

### 3.1 Spatial hierarchy now available

With the current MGE cleaning, the project already has an explicit territorial hierarchy:
- `entidad_cdmx`: state boundary of CDMX, useful for macro clipping and for OSM extraction.
- `municipios_cdmx`: boroughs, useful for administrative transfers and municipal priors.
- `localidades_cdmx`: urban and rural built localities, useful for connecting `cve_loc` with the population census.
- `ageb_urbana_cdmx`: urban intermediate unit for future sociodemographic aggregates.
- `manzanas_cdmx`: fine territorial unit that can serve for spatial validation, population, or density.

This hierarchy makes the future conversion to hexagons much clearer because an internal territorial support system already exists.

### 3.2 Point data
Point layers such as DENUE, crime, or tourism are mainly integrated through:
- counts by hexagon;
- counts by category or subcategory;
- possible densities or rates if they are later normalized by area, population, or activity.

### 3.3 Linear data
Linear layers such as transport routes, road network, or corridors can be integrated through:
- intersection with hexagons;
- contained or weighted length within the hexagon;
- counts of lines, segments, or accesses depending on the case.

OSM enters here especially, since for now it exists as a raw road network for cars and not yet as clean feature engineering.

### 3.4 Polygon data
Polygon layers such as AGEBs, municipalities, localities, blocks, risk, or spatial proxies can be integrated through:
- intersection with hexagons;
- weighting by overlap percentage;
- transfer from municipality, locality, or AGEB to the hexagon when the data does not originally live at point level.

The case of `censo_pob_operativo.parquet` is important: the table is already clean, but assignment to hexes will come later, using locality or municipality as the territorial support.

### 3.5 Aggregated non-spatial data at a fine level
The most important case here is the **Economic Census**. That set does not describe individual businesses, but aggregated cells by municipality and economic-activity level. Therefore its role is not to "join" DENUE record by record, but to provide a **municipal economic prior** that can later be used when building hexagon features.

In flow terms, the project distinguishes three moments:
- the source already clean and ready to integrate;
- the table or layer already transformed into information compatible with hexagons, which conceptually corresponds to `0_HEX_DATA`;
- the final merged table by hexagon, which conceptually corresponds to `1_DATA_HEX_MERGED`;
- and then, on top of that result, graph construction.

## 4. Feature Engineering
The project is not organized only by files, but by **families of signals** that try to describe the city as support for economic activity and commercial recommendation.

### 4.1 Economic and functional activity
DENUE and SCIAN form the base to describe:
- presence of establishments;
- nearby competition;
- commercial complementarity;
- sectoral or functional mix of the environment.

Here the role of SCIAN is fundamental because it allows deciding later whether the final aggregation works best at the level of sector, branch, sub-branch, or class, depending on the balance between interpretability and granularity.

### 4.2 Aggregated economic priors
The Economic Census enters as a different layer:
- it does not represent revenue of each POI;
- it does not represent ground truth for each business;
- it does represent aggregated productivity by municipality and economic-activity level.

For that reason, its correct use is to build signals such as:
- income per economic unit;
- income per occupied person;
- production per economic unit;
- occupied personnel per economic unit.

These signals can later enrich the hexagon as a municipal prior conditioned by economic activity, using the composition of observed POIs in each hexagon.

### 4.3 Population and housing
The population census is no longer only a conceptual source. There is now an operational table with:
- total population;
- female and male population;
- aggregated age groups;
- households and dwellings;
- both `municipio_total` and `localidad` rows.

The immediate utility of this table is not direct merge, but preparing future spatial assignment to hexes through locality or municipality.

### 4.4 Mobility and accessibility
SEMOVI provides the public-transport layer:
- routes;
- stops;
- modal variety;
- density or proximity of accessibility.

In addition, OSM already exists as raw road-network extraction for cars, ready to later become road-connectivity and accessibility variables.

### 4.5 Safety and risk
Crime and natural risk add two different dimensions:
- **safety**: friction or expected cost of the environment;
- **natural risk**: structural condition of territorial vulnerability.

These layers do not say by themselves whether an area is commercially bad, but they are part of the context that modulates desirability, exposure, and robustness of a location.

### 4.6 Urban and value proxies
Proxy layers, such as property tax or land value, function as an approximation to:
- economic intensity of the environment;
- cost or spatial status;
- viability or real-estate pressure.

They do not replace private client data, but they help introduce signals of territorial value that usually matter in location decisions.

### 4.7 Base spatial context
MGE provides the structural geometry of the system:
- administrative network;
- localities;
- AGEBs;
- blocks;
- cartographic support for future transfers.

OSM provides the raw road network and later may provide car-connectivity signals at hex scale.

### 4.8 Core composition idea
The specific sectoral mix of each hexagon should mainly emerge from the observed composition of POIs. In contrast, the Economic Census should be understood as a layer of **aggregated economic intensity** that contextualizes that composition, not as a table of revenue per business.

## 5. Spatial Architecture and Graph Construction
The project architecture follows the intuition that an urban area is not explained only by its internal attributes, but also by its relationship with the surrounding environment.

### 5.1 Nodes
Each graph node is an **H3 hexagon**. The node contains:
- the feature vector built from the spatial merge;
- its geometry or H3 identifier as spatial reference;
- and, eventually, information conditioned by business type when the system is used as a recommender.

### 5.2 Physical edges
Physical edges represent spatial neighborhood. Conceptually they can be built by:
- H3 adjacency;
- nearest neighbors;
- or a combination that guarantees connectivity and local context.

The goal of these edges is for the embedding of a hexagon to incorporate information from its immediate neighborhood and not only from its own cell.

### 5.3 Virtual edges
The capstone documents and the canvas also justify the idea of virtual edges:
- they connect hexagons that are not necessarily contiguous;
- they are based on feature similarity or urban typology;
- they expand the receptive field of the model;
- they allow connecting functionally similar zones even if they are spatially separated.

This is important because two zones may have similar commercial structure without being next to each other.

### 5.4 Final modeling artifact
The conceptual result of this phase is a graph object compatible with **PyTorch Geometric** or an equivalent structure:
- nodes = hexagons;
- edges = physical and optionally virtual relationships;
- attributes = unified feature table by hexagon.

## 6. Modeling
The project is conceived as a spatial recommendation system based on GNN, not as a road-risk classifier like `MapaSinGNN`.

### 6.1 Main model
The expected architecture is:
- an initial **MLP** layer to harmonize and project features;
- a **GNN** that learns urban embeddings of the hexagons;
- a scoring or ranking head that allows ordering zones according to the target business type.

The intuition is that the embedding should capture:
- local context;
- functional structure;
- accessibility;
- economic activity;
- and non-trivial relationships between zones.

### 6.2 Immediate product
The main output is not "this exact street" or a perfect accounting score, but a spatial recommendation useful to reduce the decision universe to promising micro-zones.

For that reason the project prioritizes:
- ranking;
- comparison between candidates;
- spatial interpretability;
- embeddings useful for exploration.

### 6.3 Future extension with private data
If in the future client data exists such as:
- revenue by branch;
- sales;
- customer flow;
- historical performance;

then the project can be extended with a second model that uses:
- features by hexagon;
- GNN embeddings;
- and real business outcomes.

That second level would make it possible to move from structural recommendation to prediction of revenue, success, or expected economic viability.

## 7. Evaluation and Deliverable
The evaluation of the system should align with the business problem and not only with an abstract metric.

### 7.1 Model evaluation
Since the goal is to recommend zones, evaluation should focus on:
- ranking quality;
- stability of recommendations;
- comparison against non-graph baselines;
- ability to find reasonable zones by urban intuition and commercial criteria.

It is not enough to optimize average error if the recommended Top-K does not make operational sense.

### 7.2 Comparison with baselines
The capstone documents already consider comparing the GNN with traditional models. This is important because:
- it forces justification of the graph’s value;
- it allows measuring whether the embeddings add information over a tabular baseline;
- it helps distinguish whether the improvement comes from the architecture or simply from the features.

### 7.3 Final deliverable for the user
The expected deliverable should include:
- a Top-K ranking of recommended hexagons;
- an interactive map or spatial visualization;
- an interpretable explanation of why certain zones appear at the top;
- and filters to narrow by business type, area, and operational restrictions.

The idea is not to replace field validation, but to make it much more focused and less intuitive.

## 8. What This Project Actually Produces
In practical terms, this project produces a spatial representation and recommendation system with three levels:

1. **Urban representation**: it converts heterogeneous CDMX sources into a comparable base by H3 hexagon.
2. **Relational representation**: it transforms those hexagons into a graph where local context and urban similarity matter.
3. **Operational translation**: it turns embeddings and scores into a prioritized list of zones for commercial expansion.

The final result is not just a table with businesses or a density map, but an **urban ontology oriented toward recommendation**:
- the city becomes a system of comparable nodes;
- each node has economic, urban, and contextual attributes;
- those nodes are connected in a graph;
- the graph learns embeddings;
- and those embeddings are translated into more informed location decisions.

In that sense, `CDMXGNN` is not only a cleaning or spatial-merge project. It is an attempt to build an intermediate layer between the urban complexity of Mexico City and the concrete decision of where to open a business.
