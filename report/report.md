---
title: "Detecting and ranking hanging glaciers from terrain and inventory data (Mischabel–Weisshorn–Dent Blanche, Valais)"
author: "Alex Gouzi"
date: "November 2026"
---

**Summary.** A random forest trained on a manual mapping of four 5 × 5 km blocks finds hanging glaciers from terrain
variables and inventory outlines, including hanging parts of large glaciers that the inventory does not separate.
Outside its training blocks, 19 of 25 randomly drawn candidates (0.76) were confirmed on orthophotos. Its 151
candidates are ranked by a geometric index. Their thermal state (cold or temperate base) is not assessed here. Code,
data versions and notebooks: <https://github.com/alexandregouzi/icefal_hanging_glaciers>.

# 1. Question and study area

Can a classifier trained on a manual mapping detect the hanging glaciers of a massif, including those contained in
larger inventory outlines, and rank them by a geometric index?

The study area is a 34 × 23 km rectangle around the Mischabel, Weisshorn and Dent Blanche ranges (LV95, E
2,608–2,642 km, N 1,090–1,113 km). It holds 127 whole glaciers of the Swiss Glacier Inventory SGI2023 (GLAMOS,
release 2026; 158.6 km²). Terrain comes from swissALTI3D (2 m, 2024), averaged exactly to 10 m. Hanging glaciers
were mapped on SWISSIMAGE 2023 orthophotos, the same year as the SGI2023 outlines of the area (Fig. 1).

The area was chosen for two reasons. It is high mountain terrain, with several summits above 4,000 m (Dom,
Weisshorn, Täschhorn): 91 % of its glacier area belongs to glaciers whose median elevation is above 3,000 m. At
these elevations hanging glaciers can be frozen to their bed; where the ice–bed interface becomes partly temperate,
meltwater may reduce the basal resistance without clear precursory signs (Faillettaz et al., 2015), the question of
the ICEFAL project. The area also holds two of the six small glaciers where Beer et al. (2026) found polythermal ice
in boreholes, Alphubel South and Chessjengletscher. Alphubel, a hanging glacier with frontal break-off on 1930
imagery (Beer et al., 2026), no longer appears hanging on the 2023 orthophotos and was neither mapped nor predicted
as hanging here.

![(a) Study area, SGI2023 outlines, mapping blocks and boreholes of Beer et al. (2026). (b) Manual mapping in
block 4 (Zinal–Moming): blind mapping and polygons added after the review. Hillshade from swissALTI3D; LV95
coordinates.](../figures/fig1_study_area.pdf){width=85%}

# 2. Methods

**Manual mapping.** Four blocks of 5 × 5 km in contrasting settings (Alphubel–Täschhorn, Weisshorn–Bisgletscher,
Fee–Allalin, Zinal–Moming; 44.4 km² of ice, 28 % of the total) were mapped exhaustively. The polygons were drawn by
hand in QGIS (version 3.42) on the SWISSIMAGE 10 cm orthophotos, streamed from swisstopo (WMTS), with the hillshade
and slope map of the DEM and the SGI2023 outlines and centre lines as reference layers; the later reviews of the
model's outputs were made in the same way. A hanging glacier is here ice whose front ends above a rock step or on a
very steep slope, so that it loses ice by break-off at its front: the avalanching glaciers of Pralong & Funk (2006).
They keep *hanging* for the unbalanced case, which must lose ice by break-off to keep a finite size; this cannot be
judged on an orthophoto, so *hanging* is used here in the broader sense. Icefalls inside a glacier were excluded:
the criterion is the continuity of the ice across the step. The decision is based on the imagery (ice cliff, rock
wall below, ice debris), never on a slope threshold, so that the slope separating the classes is a result and not an
assumption. Where the orthophotos were unclear, recent photographs and videos of the glaciers found online were used
as a complement. Each polygon carries a confidence (1–3); the upper edge of a polygon is the bergschrund or the
break in slope above the hanging part, otherwise the SGI2023 outline (protocol: `report/mapping_protocol.md`).

**Variables.** Fifteen variables per 10 m glacier pixel come from the DEM and the SGI outlines only. Eleven describe
the pixel and its 210 m neighbourhood: elevation, slope, aspect (as northness and eastness), curvature, mean and
maximum slope and relief within 210 m, distance to the glacier edge, relative elevation in the glacier and area of
the SGI unit. Four follow the steepest-descent path (D8) below the pixel: elevation lost over 200 m, steepest slope
crossed, distance to the glacier's lower edge, and height of the step below that edge. Holes in the SGI outlines
count as rock, so a rock band inside a large glacier is seen as a step.

**Classifier and validation.** Random forest (scikit-learn, 200 trees, balanced class weights). Hanging pixels are
4.4 % of the labelled ice, so skill is measured by precision–recall and average precision (AP; a random guess scores
0.044). Validation is leave-one-block-out: each block is predicted by a forest trained on the three others. A mapped
glacier counts as detected when at least 25 % of its pixels have a probability ≥ 0.5; both thresholds were fixed in
advance, not tuned.

**Review of the errors.** The 28 false-alarm patches (≥ 1 ha) of the cross-validation were then checked on the
imagery. Hanging glaciers confirmed there were redrawn following the protocol as 22 new polygons (confidence 1/2/3:
10/10/2), tagged apart from the blind mapping. Since only places predicted *hanging* were reviewed, scores with
these revised labels are an upper bound; the blind mapping remains the reference.

**Candidates and geometric index.** A forest trained on the revised labels predicts all 1.59 million glacier pixels
of the area. Connected pixels with probability ≥ 0.5 and at least 1 ha form a candidate. The geometric index, fixed
before looking at the results, is the mean percentile rank of three variables: area, mean surface slope, and fall
height (90th percentile of the step below the lower edge). A random sample of 25 candidates outside the blocks was
checked on the imagery to measure precision where the model was never trained.

# 3. Results

**The area of the inventory unit is a shortcut.** With the 11 neighbourhood variables, AP is 0.42. Adding the four
downslope variables raises it to 0.52, but this forest detects only 1 of the 12 hanging glaciers lying inside SGI
units larger than 1 km². It relies first on the area of the unit: *small unit = hanging*. Without that variable, AP
is 0.43 (0.21 to 0.59 depending on the block left out) but 9 of the 12 hanging parts of large glaciers are found,
and 17 of the 27 mapped hanging glaciers overall (precision and recall 0.44 at a threshold of 0.5). This model is
used from here on; the choice was made after seeing these detections, not planned in advance, because hanging parts
of large glaciers are the target of the question. Single variables do worse (AP 0.19 for slope, 0.37 for step height). The most important variables are the mean slope within 210 m, the elevation lost below the
pixel and the height of the step below the glacier.

**The review suggests that the blind mapping missed hanging glaciers.** Of the 28 false-alarm patches, 25 were
judged hanging glaciers missed by the mapping, 2 model errors and 1 uncertain. With the revised labels, AP rises to
0.69 for the same predictions and to 0.75 after retraining (precision 0.64, recall 0.77), and 25 of the 27
blind-mapped glaciers are detected (Fig. 2). The true skill lies between the blind (0.43) and the revised (0.75)
scores. The hanging glacier of the Weisshorn east face (block 2; 3,800–4,500 m; break-offs in 1973, 1980, 1986, 1999
and 2005; Faillettaz et al., 2011), was mapped with confidence 3, but only 20–23 % of its pixels pass the threshold
with the blind labels; it is detected with the revised labels.

![(a) Precision–recall curves of the leave-one-block-out cross-validation (14 variables) on the blind and the
revised labels, and for single variables. (b) Out-of-fold predictions in block 4 (threshold 0.5, revised
labels).](../figures/fig2_validation.pdf){width=85%}

**151 candidates over the area.** The model finds 151 candidates (8.6 km²), 110 of them outside the mapping blocks
and 105 inside glaciers larger than 1 km² (Fig. 3). Of the random sample of 25 candidates outside the blocks, 19
were hanging, 5 not hanging and 1 uncertain, counted as not hanging: precision 0.76 (Wilson 95 % interval
0.57–0.89). Four of the six negatives are among the smallest candidates (1.2–1.6 ha). Of the 20 best-ranked
candidates, 19 were confirmed and 1 stayed uncertain (not a representative check). All candidates lie above
2,940 m (median lower edge 3,440 m) and 58 % face north; those with a mid-elevation above 3,500 m make up 67 % of
the candidate area (Alpine glaciers are typically cold above ~3,500–3,800 m; Gilbert et al., 2026, preprint). Leaving out one of
the three index variables keeps a rank correlation of 0.81–0.83 with the full index, but only 9 to 16 of the top 20
stay in it: the top of the ranking depends on the weighting. Examples of well-ranked candidates are on the
Zmuttgletscher, Glacier de Zinal and Glacier de Moming (top 20 with elevation and aspect:
`report/top20_candidates.csv`).

![Candidate hanging glaciers of the study area (probability ≥ 0.5, ≥ 1 ha), coloured by quartile of the geometric
index. Numbers give the ten highest ranks (two candidates share rank 7). Dashed squares: mapping
blocks.](../figures/fig3_candidates.pdf){width=85%}

# 4. Discussion and limits

Variables describing what lies *below* the ice detect hanging glaciers, including parts of large glaciers, if the
classifier cannot use the size of the inventory unit. The review suggests that a careful visual mapping itself
misses hanging glaciers: the classifier is useful as a screening tool, with a person checking its candidates. The
ranking is geometric only: whether a candidate is frozen to its bed, and how fast this may change with warming,
requires measurements and a thermal model driven by climate data, the object of the ICEFAL project. There, the
method could pre-select hanging glaciers for field measurements or monitoring, and be transferred to the French Alps
with French glacier outlines and the IGN RGE ALTI DEM, once one block is mapped there for training. A geometric
index also misses other hazards: at Alphubel, no longer hanging, Beer et al. (2026) met pressurised water that rose
3–5 m above a borehole.

Limits: the main limit is the manual mapping itself. It was made by a single mapper without prior training in
recognising hanging glaciers, with a written protocol, a confidence level per polygon and two reviews to compensate.
Some ice may still have been labelled hanging when it is not, and some hanging glaciers missed. Ten of the 27 blind
polygons were drawn with the lowest confidence, and only 4 of them are detected. Without them, AP falls to 0.29, but
so does the share of hanging pixels (0.029): the gain over a random guess stays about tenfold. The reviews were made
while seeing the model's outlines, so the revised scores and the 0.76 precision are optimistic; a blind control,
judging the false alarms mixed with comparable patches predicted not hanging, was not made. Four blocks give only
four folds. Only ice inside the SGI2023 outlines and patches of at least 1 ha are considered: smaller hanging ice,
or ice missing from the inventory, cannot be found. The D8 path of a pixel near the side of a glacier can leave the
ice sideways over a rock wall, a possible source of false alarms. The geometric index is a relative ranking, not a
hazard score calibrated on observed ice avalanches, and it ignores ice thickness, which is unknown.

# References

- Beer, J., Jacquemart, M., Huss, M., Santin, I., Clara Racz, G., Ogier, C., Gindraux, S., Hösli, L., Moser, R.,
  Irving, J., Fischer, M. & Farinotti, D. (2026). Polythermal conditions in small glaciers in the Swiss Alps.
  *The Cryosphere* 20, 5453–5473. <https://doi.org/10.5194/tc-20-5453-2026>.
- Faillettaz, J., Funk, M. & Vincent, C. (2015). Avalanching glacier instabilities: review on processes and early
  warning perspectives. *Reviews of Geophysics* 53(2), 203–224. <https://doi.org/10.1002/2014RG000466>.
- Faillettaz, J., Funk, M. & Sornette, D. (2011). Icequakes coupled with surface displacements for predicting
  glacier break-off. *Journal of Glaciology* 57(203), 453–460. <https://doi.org/10.3189/002214311796905668>.
- Gilbert, A., Troilo, F., Gagliardini, O., Vincent, C., Perret, P., Mondardini, L., Piard, L., Laarman, O. &
  Le Meur, E. (2026). The thermal regime of the Whymper hanging glacier under climate change (Grandes Jorasses,
  4050 m a.s.l., Italy). *EGUsphere* preprint. <https://doi.org/10.5194/egusphere-2026-4058>.
- GLAMOS (2026). Swiss Glacier Inventory 2023 (SGI2023), release 2026. Glacier Monitoring Switzerland.
  <https://doi.org/10.18750/inventory.sgi2023.r2026>.
- Pralong, A. & Funk, M. (2006). On the instability of avalanching glaciers. *Journal of Glaciology* 52(176),
  31–48. <https://doi.org/10.3189/172756506781828980>.
- swisstopo. swissALTI3D (2024) and SWISSIMAGE 10 cm (2023).
