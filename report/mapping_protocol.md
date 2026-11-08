# Manual mapping protocol – hanging glaciers

Draft for the Methods section. To be checked and adjusted by the author before use.
References marked **[verify]** must be checked against the original papers.

## Purpose

The manual mapping provides the labels used to train and evaluate the classifier.
Within each completed block, every glacier pixel inside a mapped polygon is labelled
*hanging* (1) and every other glacier pixel is labelled *not hanging* (0). Areas outside
the completed blocks are not used for training; the blocks also define the folds of the
spatial cross-validation.

## Definition

A **hanging glacier** is a glacier, or part of a glacier, whose front ends above a rock step
or a very steep slope, so that ice can only leave it by detaching (serac falls or ice avalanches).
Two front types are recorded, following Alean (1985) **[verify]**:

- **cliff**: the front ends abruptly at the edge of a rock step, with a visible ice cliff or serac band;
- **ramp**: the ice rests on a steep bed and ends without an ice cliff; failure would involve a slab of the glacier.

Excluded:

- valley tongues ending on gentle terrain;
- icefalls *within* a glacier (seracs, but the ice continues downstream);
- snow patches without visible glacier ice, and debris-covered ice at the foot of rock walls.

## Avoiding circular labels

The decision to map a glacier as hanging is based on **visual evidence in the orthophotos**
(SWISSIMAGE): an ice cliff or serac band at the front, a rock wall directly below, and ice debris
downslope. The slope map is used only to locate candidates and to trace the upper limit of the
hanging part. No slope threshold is used as a criterion, so that the slope values that separate
the two classes are a result of the classifier, not an assumption of the labelling.

## What is drawn

One polygon per hanging glacier, covering the hanging ice mass:

- lower edge: the front (edge of the ice above the rock step);
- upper edge: the bergschrund or the break in slope above which the glacier becomes less steep;
  where neither is visible, the SGI2023 outline;
- lateral edges: the SGI2023 outline (snapped).

Where the hanging glacier is a separate SGI2023 unit, its outline is reused. Where it is part of a
larger outline, only the hanging part is drawn. Where the visible front has retreated from the SGI2023
outline (imagery more recent than 2021–2024), the visible front is drawn and the case is noted.

Attributes: `front_type` (cliff / ramp), `confidence` (1 = doubtful, 2 = probable, 3 = certain), `notes`.

## Mapping blocks

Mapping is exhaustive within four blocks of 5 × 5 km chosen in contrasting settings
(`src/prepare_mapping_kit.py`):

| Block | Name | LV95 extent (km) | Note |
|---|---|---|---|
| 1 | Alphubel–Täschhorn | 2629–2634 E, 1099–1104 N | contains the Alphubel boreholes |
| 2 | Weisshorn–Bisgletscher | 2617–2622 E, 1103–1108 N | |
| 3 | Fee–Allalin | 2634–2639 E, 1097–1102 N | contains the Chessjengletscher boreholes |
| 4 | Zinal–Moming | 2613–2618 E, 1098–1103 N | |

Together they cover about 44 km² of the 159 km² of glacier ice in the study extent (28 %).
A hanging glacier crossing a block edge is drawn entirely. A block is marked `done` only once all
its hanging glaciers have been mapped. The year of the SWISSIMAGE flight is recorded per block (`image_year`).

## Data and tools

- Imagery: SWISSIMAGE 10 cm, WMTS stream `ch.swisstopo.swissimage` (swisstopo), viewed in QGIS.
- Terrain: 10 m DEM from swissALTI3D 2024 (hillshade) and the derived slope map.
- Reference: SGI2023 outlines and centre lines (GLAMOS 2026).
- Output: `data/raw/manual_mapping.gpkg` (layers `hanging_glaciers`, `blocks`), LV95 (EPSG:2056).
