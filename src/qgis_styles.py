"""QGIS styles (QML) for the manual mapping kit.

Kept in a separate file so that prepare_mapping_kit.py stays readable.
Vector styles are stored inside the GeoPackages (table `layer_styles`) and
raster styles as `.qml` files next to the GeoTIFFs: QGIS applies both automatically
when the layer is added.
"""

from xml.sax.saxutils import escape

HEADER = "<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>\n"


def _fill_symbol(name, fill_rgba, outline_rgba, width=0.6, outline_style="solid", fill_style="solid"):
    return f"""
   <symbol type="fill" name="{name}" alpha="1" clip_to_extent="1" force_rhr="0">
    <layer class="SimpleFill" enabled="1" locked="0" pass="0">
     <Option type="Map">
      <Option name="color" type="QString" value="{fill_rgba}"/>
      <Option name="style" type="QString" value="{fill_style}"/>
      <Option name="outline_color" type="QString" value="{outline_rgba}"/>
      <Option name="outline_style" type="QString" value="{outline_style}"/>
      <Option name="outline_width" type="QString" value="{width}"/>
      <Option name="outline_width_unit" type="QString" value="MM"/>
     </Option>
    </layer>
   </symbol>"""


def _value_map(field, values):
    items = "".join(
        f'<Option type="Map"><Option name="{label}" type="QString" value="{value}"/></Option>'
        for value, label in values
    )
    return f"""
  <field name="{field}" configurationFlags="NoFlag">
   <editWidget type="ValueMap">
    <config><Option type="Map"><Option name="map" type="List">{items}</Option></Option></config>
   </editWidget>
  </field>"""


def _range(field, vmin, vmax):
    return f"""
  <field name="{field}" configurationFlags="NoFlag">
   <editWidget type="Range">
    <config><Option type="Map">
     <Option name="Min" type="int" value="{vmin}"/>
     <Option name="Max" type="int" value="{vmax}"/>
     <Option name="Step" type="int" value="1"/>
     <Option name="Style" type="QString" value="SpinBox"/>
     <Option name="AllowNull" type="bool" value="true"/>
    </Option></config>
   </editWidget>
  </field>"""


def _multiline(field):
    return f"""
  <field name="{field}" configurationFlags="NoFlag">
   <editWidget type="TextEdit">
    <config><Option type="Map"><Option name="IsMultiline" type="bool" value="true"/></Option></config>
   </editWidget>
  </field>"""


def _labels(field, rgb, size=10):
    return f"""
 <labeling type="simple">
  <settings calloutType="simple">
   <text-style fieldName="{field}" isExpression="0" fontSize="{size}" fontSizeUnit="Point"
               textColor="{rgb},255" textOpacity="1" fontWeight="75" fontFamily="Arial">
    <text-buffer bufferDraw="1" bufferSize="1" bufferSizeUnits="MM" bufferColor="255,255,255,255" bufferOpacity="1"/>
   </text-style>
   <placement placement="1" offsetType="0"/>
   <rendering obstacle="1" scaleVisibility="0" drawLabels="1"/>
  </settings>
 </labeling>"""


def hanging_glaciers_qml():
    """Red semi-transparent polygons; form with cliff/ramp, current/former and initial/review lists and a 1–3 confidence box.

    `source` tells the polygons of the initial, blind mapping from those drawn after reviewing the
    model's false alarms; new polygons default to 'review'.
    """
    return HEADER + f"""<qgis version="3.34" styleCategories="Symbology|Fields|Forms">
 <renderer-v2 type="singleSymbol" symbollevels="0" enableorderby="0" forceraster="0">
  <symbols>{_fill_symbol("0", "227,73,72,90", "227,73,72,255", 0.6)}
  </symbols>
 </renderer-v2>
 <fieldConfiguration>{_value_map("front_type", [("cliff", "cliff"), ("ramp", "ramp")])}{_value_map("state", [("current", "current"), ("former", "former")])}{_range("confidence", 1, 3)}{_multiline("notes")}{_value_map("source", [("initial", "initial (blind mapping)"), ("review", "review (after the false alarms)")])}
 </fieldConfiguration>
 <defaults>
  <default field="state" expression="'current'" applyOnUpdate="0"/>
  <default field="source" expression="'review'" applyOnUpdate="0"/>
 </defaults>
 <constraints>
  <constraint field="front_type" constraints="1" notnull_strength="1" unique_strength="0" exp_strength="0"/>
  <constraint field="confidence" constraints="1" notnull_strength="1" unique_strength="0" exp_strength="0"/>
 </constraints>
</qgis>
"""


def blocks_qml():
    """Block outlines: dashed orange while 'todo', green once 'done'; labelled with their name."""
    return HEADER + f"""<qgis version="3.34" styleCategories="Symbology|Labeling|Fields|Forms">
 <renderer-v2 type="categorizedSymbol" attr="status" symbollevels="0" enableorderby="0" forceraster="0">
  <categories>
   <category value="todo" symbol="0" label="to do" render="true"/>
   <category value="done" symbol="1" label="done" render="true"/>
  </categories>
  <symbols>{_fill_symbol("0", "0,0,0,0", "235,104,52,255", 1.0, "dash", "no")}{_fill_symbol("1", "0,0,0,0", "0,131,0,255", 1.0, "solid", "no")}
  </symbols>
 </renderer-v2>{_labels("name", "235,104,52", 11)}
 <fieldConfiguration>{_value_map("status", [("todo", "to do"), ("done", "done")])}{_range("image_year", 2015, 2026)}{_multiline("notes")}
 </fieldConfiguration>
</qgis>
"""


def glaciers_qml():
    """SGI outlines: no fill, blue outline, glacier names as labels."""
    return HEADER + f"""<qgis version="3.34" styleCategories="Symbology|Labeling">
 <renderer-v2 type="singleSymbol" symbollevels="0" enableorderby="0" forceraster="0">
  <symbols>{_fill_symbol("0", "0,0,0,0", "42,120,214,255", 0.5, "solid", "no")}
  </symbols>
 </renderer-v2>{_labels("name", "42,120,214", 8)}
</qgis>
"""


def centerlines_qml():
    """SGI centre lines (flow direction): thin dashed blue lines."""
    return HEADER + """<qgis version="3.34" styleCategories="Symbology">
 <renderer-v2 type="singleSymbol" symbollevels="0" enableorderby="0" forceraster="0">
  <symbols>
   <symbol type="line" name="0" alpha="1" clip_to_extent="1" force_rhr="0">
    <layer class="SimpleLine" enabled="1" locked="0" pass="0">
     <Option type="Map">
      <Option name="line_color" type="QString" value="42,120,214,255"/>
      <Option name="line_style" type="QString" value="dash"/>
      <Option name="line_width" type="QString" value="0.4"/>
      <Option name="line_width_unit" type="QString" value="MM"/>
     </Option>
    </layer>
   </symbol>
  </symbols>
 </renderer-v2>
</qgis>
"""


def boreholes_qml():
    """glenglat boreholes: orange dots with a white outline."""
    return HEADER + """<qgis version="3.34" styleCategories="Symbology">
 <renderer-v2 type="singleSymbol" symbollevels="0" enableorderby="0" forceraster="0">
  <symbols>
   <symbol type="marker" name="0" alpha="1" clip_to_extent="1" force_rhr="0">
    <layer class="SimpleMarker" enabled="1" locked="0" pass="0">
     <Option type="Map">
      <Option name="color" type="QString" value="235,104,52,255"/>
      <Option name="name" type="QString" value="circle"/>
      <Option name="outline_color" type="QString" value="255,255,255,255"/>
      <Option name="outline_width" type="QString" value="0.3"/>
      <Option name="size" type="QString" value="2.2"/>
      <Option name="size_unit" type="QString" value="MM"/>
     </Option>
    </layer>
   </symbol>
  </symbols>
 </renderer-v2>
</qgis>
"""


def slope_qml():
    """Slope classes: transparent below 30°, then yellow / orange / red; 70 % opacity."""
    classes = [  # (upper bound in degrees, colour, alpha 0–255, label)
        (30, "#ffffff", 0, "< 30°"),
        (40, "#eda100", 255, "30–40°"),
        (50, "#eb6834", 255, "40–50°"),
        (90, "#b3001b", 255, "> 50°"),
    ]
    items = "\n".join(
        f'       <item value="{v}" color="{c}" alpha="{a}" label="{escape(lab)}"/>' for v, c, a, lab in classes
    )
    return HEADER + f"""<qgis version="3.34" styleCategories="Symbology">
 <pipe>
  <rasterrenderer type="singlebandpseudocolor" band="1" opacity="0.7" alphaBand="-1"
                  classificationMin="0" classificationMax="90">
   <rastershader>
    <colorrampshader colorRampType="DISCRETE" classificationMode="1" clip="0">
{items}
    </colorrampshader>
   </rastershader>
  </rasterrenderer>
 </pipe>
 <blendMode>0</blendMode>
</qgis>
"""


def dem_hillshade_qml():
    """DEM shown as a hillshade blended with 'multiply' over the imagery below."""
    return HEADER + """<qgis version="3.34" styleCategories="Symbology">
 <pipe>
  <rasterrenderer type="hillshade" band="1" opacity="1" alphaBand="-1"
                  azimuth="315" angle="45" zfactor="1" multidirection="1"/>
 </pipe>
 <blendMode>6</blendMode>
</qgis>
"""


def false_alarms_qml():
    """False-alarm patches to review: purple outline, labelled with their number; verdict list in the form."""
    verdicts = [("missed_hanging", "hanging glacier missed by the mapping"),
                ("model_error", "not a hanging glacier (model error)"),
                ("unsure", "unsure"),
                ("redrawn", "redrawn as a polygon in manual_mapping (source = review)")]
    return HEADER + f"""<qgis version="3.34" styleCategories="Symbology|Labeling|Fields|Forms">
 <renderer-v2 type="singleSymbol" symbollevels="0" enableorderby="0" forceraster="0">
  <symbols>{_fill_symbol("0", "122,47,214,40", "122,47,214,255", 0.8)}
  </symbols>
 </renderer-v2>{_labels("patch_id", "122,47,214", 11)}
 <fieldConfiguration>{_value_map("verdict", verdicts)}{_multiline("notes")}
 </fieldConfiguration>
</qgis>
"""


def candidates_to_check_qml():
    """Candidates to check: thick green outline, labelled with their rank; verdict list in the form."""
    verdicts = [("hanging", "hanging glacier"), ("not_hanging", "not a hanging glacier"), ("unsure", "unsure")]
    return HEADER + f"""<qgis version="3.34" styleCategories="Symbology|Labeling|Fields|Forms">
 <renderer-v2 type="singleSymbol" symbollevels="0" enableorderby="0" forceraster="0">
  <symbols>{_fill_symbol("0", "27,175,122,40", "27,175,122,255", 1.0)}
  </symbols>
 </renderer-v2>{_labels("rank", "0,110,70", 11)}
 <fieldConfiguration>{_value_map("verdict", verdicts)}{_multiline("notes")}
 </fieldConfiguration>
</qgis>
"""


def candidates_qml():
    """All candidates: thin orange outline, no fill."""
    return HEADER + f"""<qgis version="3.34" styleCategories="Symbology">
 <renderer-v2 type="singleSymbol" symbollevels="0" enableorderby="0" forceraster="0">
  <symbols>{_fill_symbol("0", "0,0,0,0", "235,104,52,255", 0.4, "solid", "no")}
  </symbols>
 </renderer-v2>
</qgis>
"""
