"""
tris_to_quads_ui.py - UI module for Triangles to Quads
Part of SBTools for Maya.

Menu registration, option window, and optionVar management.
"""

import maya.cmds as cmds
import math


# ============================================================================
# OptionVar Keys and Defaults
# ============================================================================

OPTVAR_PREFIX = "SBTools_T2Q_"

DEFAULTS = {
    "angleFaceThreshold": 40.0,  # degrees
    "angleShapeThreshold": 40.0,  # degrees
    "keepUVBoundary": 1,  # on
    "keepMaterialBoundary": 1,  # on
    "keepSharpEdge": 0,  # off
    "topoInfluence": 1.0,  # 0=off, 1=default, 2=max
}

WINDOW_NAME = "sbToolsT2QOptionsWindow"


# ============================================================================
# OptionVar Management
# ============================================================================


def _optvar_key(name):
    return OPTVAR_PREFIX + name


def get_option(name):
    """Get a saved option value, or return the default."""
    key = _optvar_key(name)
    if cmds.optionVar(exists=key):
        return cmds.optionVar(query=key)
    return DEFAULTS[name]


def set_option(name, value):
    """Save an option value to optionVar."""
    key = _optvar_key(name)
    if isinstance(value, float):
        cmds.optionVar(floatValue=(key, value))
    elif isinstance(value, int):
        cmds.optionVar(intValue=(key, value))


def reset_options():
    """Reset all options to their default values."""
    for name, value in DEFAULTS.items():
        set_option(name, value)


# ============================================================================
# Execute
# ============================================================================


def execute_with_current_settings(*args):
    """Run the algorithm using the currently saved optionVar settings."""
    import tris_to_quads

    tris_to_quads.run(
        angle_face_threshold=math.radians(get_option("angleFaceThreshold")),
        angle_shape_threshold=math.radians(get_option("angleShapeThreshold")),
        keep_uv_boundary=bool(get_option("keepUVBoundary")),
        keep_sharp_edge=bool(get_option("keepSharpEdge")),
        keep_material_boundary=bool(get_option("keepMaterialBoundary")),
        topo_influence=float(get_option("topoInfluence")),
    )


# ============================================================================
# Options Window
# ============================================================================


def _save_from_ui(face_slider, shape_slider, uv_cb, mat_cb, sharp_cb, ti_slider):
    """Read current UI values and save them to optionVar."""
    set_option(
        "angleFaceThreshold",
        cmds.floatSliderGrp(face_slider, query=True, value=True),
    )
    set_option(
        "angleShapeThreshold",
        cmds.floatSliderGrp(shape_slider, query=True, value=True),
    )
    set_option(
        "keepUVBoundary",
        int(cmds.checkBoxGrp(uv_cb, query=True, value1=True)),
    )
    set_option(
        "keepMaterialBoundary",
        int(cmds.checkBoxGrp(mat_cb, query=True, value1=True)),
    )
    set_option(
        "keepSharpEdge",
        int(cmds.checkBoxGrp(sharp_cb, query=True, value1=True)),
    )
    set_option(
        "topoInfluence",
        cmds.floatSliderGrp(ti_slider, query=True, value=True),
    )


def show_options_window(*args):
    """Show the Triangles to Quads option window (Maya standard style)."""
    if cmds.window(WINDOW_NAME, exists=True):
        cmds.deleteUI(WINDOW_NAME)

    window = cmds.window(
        WINDOW_NAME,
        title="Triangles to Quads Options",
        widthHeight=(420, 290),
        sizeable=True,
    )

    # --- Menu bar with Edit > Reset ---
    cmds.menuBarLayout()
    cmds.menu(label="Edit")

    # Forward declarations so the reset closure can reference them
    face_slider_ref = [None]
    shape_slider_ref = [None]
    uv_cb_ref = [None]
    mat_cb_ref = [None]
    sharp_cb_ref = [None]
    ti_slider_ref = [None]

    def _on_reset(*args):
        reset_options()
        cmds.floatSliderGrp(
            face_slider_ref[0], edit=True, value=DEFAULTS["angleFaceThreshold"]
        )
        cmds.floatSliderGrp(
            shape_slider_ref[0], edit=True, value=DEFAULTS["angleShapeThreshold"]
        )
        cmds.checkBoxGrp(
            uv_cb_ref[0], edit=True, value1=bool(DEFAULTS["keepUVBoundary"])
        )
        cmds.checkBoxGrp(
            mat_cb_ref[0], edit=True, value1=bool(DEFAULTS["keepMaterialBoundary"])
        )
        cmds.checkBoxGrp(
            sharp_cb_ref[0], edit=True, value1=bool(DEFAULTS["keepSharpEdge"])
        )
        cmds.floatSliderGrp(
            ti_slider_ref[0], edit=True, value=DEFAULTS["topoInfluence"]
        )

    cmds.menuItem(label="Reset Settings", command=_on_reset)
    cmds.setParent("..")

    # --- Main form layout ---
    form = cmds.formLayout()
    content = cmds.columnLayout(adjustableColumn=True)

    cmds.separator(height=10, style="none")

    face_slider = cmds.floatSliderGrp(
        label="Face Normal Angle",
        field=True,
        minValue=0.0,
        maxValue=180.0,
        fieldMinValue=0.0,
        fieldMaxValue=180.0,
        value=get_option("angleFaceThreshold"),
        columnWidth3=(150, 60, 170),
        annotation="Maximum face normal angle difference (degrees). "
        "Edges between faces whose normals differ by more than this are kept.",
    )
    face_slider_ref[0] = face_slider

    shape_slider = cmds.floatSliderGrp(
        label="Shape Angle",
        field=True,
        minValue=0.0,
        maxValue=180.0,
        fieldMinValue=0.0,
        fieldMaxValue=180.0,
        value=get_option("angleShapeThreshold"),
        columnWidth3=(150, 60, 170),
        annotation="Maximum corner angle deviation from 90 degrees. "
        "Edges that would create badly-shaped quads are kept.",
    )
    shape_slider_ref[0] = shape_slider

    cmds.separator(height=10, style="in")

    uv_cb = cmds.checkBoxGrp(
        label="",
        label1="Keep UV Boundary",
        value1=bool(get_option("keepUVBoundary")),
        columnWidth2=(150, 230),
        annotation="Prevent merging across UV seams",
    )
    uv_cb_ref[0] = uv_cb

    mat_cb = cmds.checkBoxGrp(
        label="",
        label1="Keep Material Boundary",
        value1=bool(get_option("keepMaterialBoundary")),
        columnWidth2=(150, 230),
        annotation="Prevent merging across material boundaries",
    )
    mat_cb_ref[0] = mat_cb

    sharp_cb = cmds.checkBoxGrp(
        label="",
        label1="Keep Sharp Edge",
        value1=bool(get_option("keepSharpEdge")),
        columnWidth2=(150, 230),
        annotation="Prevent merging across hard/sharp edges",
    )
    sharp_cb_ref[0] = sharp_cb

    cmds.separator(height=10, style="in")

    ti_slider = cmds.floatSliderGrp(
        label="Topology Influence",
        field=True,
        minValue=0.0,
        maxValue=2.0,
        fieldMinValue=0.0,
        fieldMaxValue=2.0,
        value=get_option("topoInfluence"),
        columnWidth3=(150, 60, 170),
        annotation="Controls how much neighboring quad quality influences merging. "
        "0=off (pure error-based), 1=standard, 2=aggressive grid flow.",
    )
    ti_slider_ref[0] = ti_slider

    cmds.setParent("..")  # end columnLayout

    # --- Button row ---
    cmds.separator(height=10, style="in")

    def _on_apply_close(*args):
        _save_from_ui(face_slider, shape_slider, uv_cb, mat_cb, sharp_cb, ti_slider)
        execute_with_current_settings()
        cmds.deleteUI(window)

    def _on_apply(*args):
        _save_from_ui(face_slider, shape_slider, uv_cb, mat_cb, sharp_cb, ti_slider)
        execute_with_current_settings()

    def _on_close(*args):
        cmds.deleteUI(window)

    btn_row = cmds.rowLayout(
        numberOfColumns=3,
        columnWidth3=(133, 133, 133),
        columnAlign3=("center", "center", "center"),
        columnAttach3=("both", "both", "both"),
    )
    cmds.button(label="Apply and Close", command=_on_apply_close)
    cmds.button(label="Apply", command=_on_apply)
    cmds.button(label="Close", command=_on_close)
    cmds.setParent("..")  # end rowLayout

    # --- Attach to form ---
    cmds.formLayout(
        form,
        edit=True,
        attachForm=[
            (content, "top", 0),
            (content, "left", 0),
            (content, "right", 0),
            (btn_row, "left", 10),
            (btn_row, "right", 10),
            (btn_row, "bottom", 10),
        ],
        attachControl=[
            (content, "bottom", 5, btn_row),
        ],
    )

    cmds.showWindow(window)


# ============================================================================
# Menu Building
# ============================================================================

MENU_NAME = "SBToolsMenu"


def build_menu():
    """Build or rebuild the SBTools top-level menu in Maya's main menu bar."""
    if cmds.menu(MENU_NAME, exists=True):
        cmds.deleteUI(MENU_NAME)

    cmds.menu(
        MENU_NAME,
        label="SBTools",
        parent="MayaWindow",
        tearOff=True,
    )

    cmds.menuItem(
        label="Triangles to Quads",
        image="polyQuad.png",
        command=execute_with_current_settings,
        annotation="Convert triangles to quads on selected mesh(es). "
        "Shift+click or use the option box to change settings.",
    )

    # Option box (the □ on the right of the menu item)
    cmds.menuItem(
        optionBox=True,
        command=show_options_window,
    )
