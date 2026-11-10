# Manual mapping protocol – hanging glaciers

Protocol of the manual mapping used as training and evaluation labels.

## Purpose

The manual mapping provides the labels used to train and evaluate the classifier.
Within each completed block, every glacier pixel inside a mapped polygon is labelled
*hanging* (1) and every other glacier pixel is labelled *not hanging* (0). Areas outside
the completed blocks are not used for training; the blocks also define the folds of the
spatial cross-validation.

## Definition

A **hanging glacier** is a glacier, or part of a glacier, whose front ends above a rock step
or on a very steep slope, so that it loses ice by break-off at its front (serac falls or ice avalanches):
the avalanching glaciers of Pralong & Funk (2006). Two front types are recorded, after the two types of
ice-avalanche starting zones of Alean (1985):

- **cliff** (Alean's type II): the ice breaks off where the bed steepens abruptly, at the edge of a rock step,
  with a visible ice cliff or serac band;
- **ramp** (Alean's type I, a steep bed of fairly constant slope; the word *ramp* is from Pralong & Funk 2006):
  the ice ends without an ice cliff; failure would involve a slab of the glacier.

Excluded:

- valley tongues ending on gentle terrain;
- icefalls *within* a glacier (seracs, but the ice continues downstream);
- snow patches without visible glacier ice, and debris-covered ice at the foot of rock walls.

Icefalls versus hanging glaciers: the deciding criterion is the **continuity of the ice across the
rock step**. Where the ice is continuous from the top to the foot of the step, the seracs form an icefall
within the glacier (not hanging). Where a band of bare rock interrupts the ice at the step, the upper part
now ends above a rock wall and is mapped as a hanging glacier (the lower part is a regenerated glacier).
Ice detaching laterally over a rock wall is mapped as hanging for that sector.

Former hanging glaciers: a glacier whose front has clearly retreated from the lip of the rock step that it
used to overhang is recorded with `state = former`, only when this is obvious in the 2023 imagery. Former
hanging glaciers cannot be identified reliably from a single image and differ from current ones by their
history rather than their present geometry; they are therefore **not used as training labels** and are
analysed separately.

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
larger outline, only the hanging part is drawn. Where the visible front differs from the SGI2023
outline (both date from 2023 in the mapping blocks, so differences should be rare), the visible front
is drawn and the case is noted.

Attributes: `front_type` (cliff / ramp), `state` (current / former; default current),
`confidence` (1 = doubtful, 2 = probable, 3 = certain), `notes`.
Labels are clipped to the SGI2023 outlines. The classifier is trained on all polygons, and a sensitivity
run excludes the polygons with confidence 1.

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
its hanging glaciers have been mapped. The year of the SWISSIMAGE flight is recorded per block (`image_year`): 2023 for all four blocks,
the same year as the SGI2023 outlines in these blocks.

## Data and tools

- Imagery: SWISSIMAGE 10 cm, WMTS stream `ch.swisstopo.swissimage` (swisstopo), viewed in QGIS.
- Where the orthophotos were unclear: recent photographs and videos of the glaciers found online.
- Terrain: 10 m DEM from swissALTI3D 2024 (hillshade) and the derived slope map.
- Reference: SGI2023 outlines and centre lines (GLAMOS 2026).
- Output: `data/raw/manual_mapping.gpkg` (layers `hanging_glaciers`, `blocks`), LV95 (EPSG:2056).

## Review of the false alarms

After the first cross-validation, the patches of at least 1 ha predicted hanging (out-of-fold probability ≥ 0.5)
outside the mapped polygons were checked on SWISSIMAGE with the same rules (`src/prepare_false_alarm_review.py`,
`data/raw/false_alarms_review.gpkg`). Each patch received a verdict: `missed_hanging`, `model_error`, `unsure`, or
`redrawn` when the author drew the hanging glacier as a new polygon (`source = review` in `manual_mapping.gpkg`;
the polygons of the blind mapping have `source = initial`). The outlines of the patches, produced by the model,
are never used as labels.

Because only places predicted *hanging* were reviewed, the corrections all favour the model. The evaluation
therefore uses the initial labels as the reference; scores with the revised labels (all polygons, reviewed patches
judged hanging or unsure but not redrawn excluded) are reported as an upper bound (notebook 04).

## References

- Alean, J. (1985). Ice avalanches: some empirical information about their formation and reach.
  *Journal of Glaciology* 31(109), 324–333. <https://doi.org/10.3189/S0022143000006663>.
- GLAMOS (2026). Swiss Glacier Inventory 2023 (SGI2023), release 2026. Glacier Monitoring Switzerland.
  <https://doi.org/10.18750/inventory.sgi2023.r2026>.
- Pralong, A. & Funk, M. (2006). On the instability of avalanching glaciers. *Journal of Glaciology* 52(176),
  31–48. <https://doi.org/10.3189/172756506781828980>.
