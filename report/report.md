---
title: "Detecting and ranking hanging glaciers from terrain data: a test on the Mischabel–Weisshorn massif (Valais)"
author: "Alex Gouzi"
date: "November 2026"
---

**Summary.** A random forest trained on a manual mapping of four 5 × 5 km blocks finds hanging glaciers from
terrain variables alone, including hanging parts of large glaciers that the inventory does not separate. Outside
its training blocks, 18 of 22 randomly drawn candidates (0.82) were confirmed on orthophotos. Its 151 candidates
are ranked by a geometric index. Their thermal state (cold or temperate base) is not assessed here. Code, data
versions and notebooks: <https://github.com/alexandregouzi/icefal_hanging_glaciers>.

# 1. Question and study area

Can a classifier trained on a manual mapping detect the hanging glaciers of a massif, including those contained in
larger inventory outlines, and rank them by a geometric index?

The study area is a 34 × 23 km rectangle around the Mischabel and Weisshorn ranges (LV95, E 2,608–2,642 km,
N 1,090–1,113 km). It holds 127 whole glaciers of the Swiss Glacier Inventory SGI2023 (GLAMOS, release 2026;
158.6 km²). Terrain comes from swissALTI3D (2 m, 2024), averaged exactly to 10 m. Hanging glaciers were mapped on
SWISSIMAGE 2023 orthophotos, the same year as the SGI2023 outlines of the area (Fig. 1).

The area was chosen for two reasons. It is high mountain terrain, with several summits above 4,000 m (Dom,
Weisshorn, Täschhorn): 91 % of its glacier area belongs to glaciers whose median elevation is above 3,000 m. At these
elevations hanging glaciers can be frozen to their bed, and their stability depends on this basal state: where the
ice–bed interface becomes partly temperate, meltwater may reduce the basal resistance, with no clear precursory
signs, so that the thermal regime has to be monitored (Faillettaz et al., 2015). This is the focus of the ICEFAL
project. The area also holds two of the six small glaciers where Beer et al. (2026) measured ice temperatures in
boreholes, Alphubel South and Chessjengletscher (a third, Hohsaasgletscher, lies 1.5 km east of the area). They
found polythermal ice in these glaciers, with a bed still frozen at Alphubel. Historical imagery from 1930 shows
Alphubel as a much thicker hanging glacier with a prominent frontal break-off (Beer et al., 2026); on the 2023
orthophotos it no longer appears to be hanging, and it was neither mapped nor predicted as hanging in this study.

![(a) Study area, SGI2023 glacier outlines, the four mapping blocks and the boreholes of Beer et al. (2026) on
Alphubel and Chessjengletscher. (b) Manual mapping in block 4 (Zinal–Moming): hanging glaciers of the blind mapping
and those added after the review of the false alarms. Hillshade from swissALTI3D; coordinates in the Swiss LV95
system (EPSG:2056).](../figures/fig1_study_area.pdf)

# 2. Methods

**Manual mapping.** Four blocks of 5 × 5 km in contrasting settings (Alphubel–Täschhorn, Weisshorn–Bisgletscher,
Fee–Allalin, Zinal–Moming; 44.4 km² of ice, 28 % of the total) were mapped exhaustively. The polygons were drawn by
hand in QGIS (version 3.42) on the SWISSIMAGE 10 cm orthophotos, streamed from swisstopo (WMTS), with the hillshade
and slope map of the DEM and the SGI2023 outlines and centre lines as reference layers; the later reviews of the
model's outputs were made in the same way. A hanging glacier is here ice whose front ends above a rock step or on a
very steep slope, so that it loses ice by break-off at its front (the avalanching glaciers of Pralong & Funk, 2006).
Icefalls inside a glacier were excluded: the criterion is the continuity of the ice across the step. The decision is
based on the imagery (ice cliff, rock wall below, ice debris), never on a slope threshold, so that the slope
separating the classes is a result and not an assumption. Where the orthophotos were unclear, recent photographs and
videos of the glaciers found online were used as a complement. Each polygon carries a confidence (1–3); the protocol
is in `report/mapping_protocol.md`.

**Variables.** Fifteen variables per 10 m glacier pixel come from the DEM and the SGI outlines only: elevation,
slope, aspect, curvature, slope and relief within 210 m, distance to the glacier edge, relative elevation in the
glacier, area of the SGI unit, and four variables that follow the steepest-descent path below the pixel: elevation
lost over 200 m, steepest slope crossed, distance to the glacier's lower edge, and height of the step below that
edge. Holes in the SGI outlines count as rock, so a rock band inside a large glacier is seen as a step.

**Classifier and validation.** Random forest (scikit-learn, 200 trees, balanced class weights). Hanging pixels are
4.4 % of the labelled ice, so skill is measured by precision–recall and average precision (AP; a random guess
scores 0.044). Validation is leave-one-block-out: each block is predicted by a forest trained on the three others.
A mapped glacier counts as detected when at least 25 % of its pixels have a probability ≥ 0.5.

**Review of the errors.** The 28 false-alarm patches (≥ 1 ha) of the cross-validation were then checked on the
imagery. Hanging glaciers confirmed there were redrawn following the protocol as new polygons, tagged apart from
the blind mapping. Since only places predicted *hanging* were reviewed, scores with these revised labels are an
upper bound; the blind mapping remains the reference.

**Candidates and geometric index.** A forest trained on the revised labels predicts all 1.59 million glacier
pixels of the area. Connected pixels with probability ≥ 0.5 and at least 1 ha form a candidate. The geometric
index, fixed before looking at the results, is the mean percentile rank of three variables: area, mean surface
slope, and fall height (90th percentile of the step below the lower edge). A random sample of 25 candidates
outside the blocks was checked on the imagery to measure precision where the model was never trained.

# 3. Results

**The area of the inventory unit is a shortcut.** With the 11 neighbourhood variables, AP is 0.42. Adding the
four downslope variables raises it to 0.52, but this forest detects only 1 of the 12 hanging glaciers lying inside
SGI units larger than 1 km². It relies first on the area of the unit: *small unit = hanging*. Without that
variable, AP is 0.43 but 9 of the 12 hanging parts of large glaciers are found, and 17 of the 27 mapped hanging
glaciers overall (precision and recall 0.44 at a threshold of 0.5). This model is used from here on. It clearly
beats single variables: slope alone gives AP 0.19, the step height alone 0.37. The most important variables are
the mean slope within 210 m, the elevation lost below the pixel and the height of the step below the glacier.

**The blind mapping missed hanging glaciers.** Of the 28 false-alarm patches, 25 were hanging glaciers missed by
the mapping, 2 were model errors and 1 stayed uncertain. With the revised labels, AP rises to 0.69 for the same
predictions and to 0.75 after retraining (precision 0.64, recall 0.77), and 25 of the 27 blind-mapped glaciers
are detected (Fig. 2). The true skill lies between the blind (0.43) and the revised (0.75) scores.

![(a) Precision–recall curves of the leave-one-block-out cross-validation (14 variables), scored on the blind
labels and on the labels revised after the review of the false alarms, compared with single variables. AP: average
precision. (b) Out-of-fold predictions in block 4 at a threshold of 0.5, scored on the revised
labels.](../figures/fig2_validation.pdf)

**151 candidates over the massif.** The model finds 151 candidates (8.6 km²), 110 of them outside the mapping
blocks and 105 inside glaciers larger than 1 km² (Fig. 3). In the random sample outside the blocks, 18 of 22
judged candidates were hanging glaciers: precision 0.82 (Wilson 95 % interval 0.61–0.93). The three negatives
include two of the smallest candidates (1.2–1.3 ha). The best-ranked candidates lie on the Zmuttgletscher,
Glacier de Zinal, Glacier de Moming, Kingletscher, Hohbalmgletscher and Bisgletscher (`report/top20_candidates.csv`).
Leaving out one of the three index variables keeps a rank correlation of 0.81–0.83 with the full index, but only
9 to 16 of the top 20 stay in it: the top of the ranking depends on the weighting.

![Candidate hanging glaciers of the massif (probability ≥ 0.5, ≥ 1 ha), coloured by quartile of the geometric
index. Numbers give the ten highest ranks (two candidates share rank 7). Dashed squares: mapping
blocks.](../figures/fig3_candidates.pdf)

# 4. Discussion and limits

Terrain variables that describe what lies *below* the ice detect hanging glaciers, including hanging parts of large
inventory outlines, if the classifier is kept from using the size of the inventory unit. The review shows that a
careful visual mapping itself misses many hanging glaciers: the classifier is useful as a screening tool, with a
person checking its candidates. The ranking is geometric only. Whether a candidate is frozen to its bed or at the
melting point, and how fast this may change with warming, was not assessed: it requires measurements on each
glacier, such as the boreholes of Beer et al. (2026) on Alphubel and Chessjengletscher, and a thermal model driven
by climate data, which is the object of the ICEFAL project.

Limits: the main limit is the manual mapping itself. It was made by a single, non-expert mapper with little
experience in recognising hanging glaciers, so some ice may have been labelled hanging when it is not, and some hanging glaciers or parts of glaciers may
have been missed; the review of the false alarms shows that the second case did occur. These errors affect both the
training labels and the scores. The reviews were also made while seeing the model's outlines, so the revised scores
and the 0.82 precision are optimistic. Four blocks give only four folds. The geometric index is a relative ranking, not a
hazard score calibrated on observed ice avalanches, and it ignores ice thickness, which is unknown. The Alphubel
boreholes lie on a glacier that was hanging in 1930 but is no longer classed as hanging (Section 1), so they do not
document the thermal state of a present-day hanging glacier.

# References

- Beer, J., Jacquemart, M., Huss, M., Santin, I., Clara Racz, G., Ogier, C., Gindraux, S., Hösli, L., Moser, R.,
  Irving, J., Fischer, M. & Farinotti, D. (2026). Polythermal conditions in small glaciers in the Swiss Alps.
  *The Cryosphere* 20, 5453–5473. <https://doi.org/10.5194/tc-20-5453-2026>.
- Faillettaz, J., Funk, M. & Vincent, C. (2015). Avalanching glacier instabilities: review on processes and early
  warning perspectives. *Reviews of Geophysics* 53(2), 203–224. <https://doi.org/10.1002/2014RG000466>.
- GLAMOS (2026). Swiss Glacier Inventory 2023 (SGI2023), release 2026. Glacier Monitoring Switzerland.
  <https://doi.org/10.18750/inventory.sgi2023.r2026>.
- Pralong, A. & Funk, M. (2006). On the instability of avalanching glaciers. *Journal of Glaciology* 52(176),
  31–48. <https://doi.org/10.3189/172756506781828980>.
- swisstopo. swissALTI3D (2024) and SWISSIMAGE 10 cm (2023).
