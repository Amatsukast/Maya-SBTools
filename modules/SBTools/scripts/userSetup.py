"""
userSetup.py - SBTools for Maya
Automatically registers the SBTools menu when Maya starts.

This file is executed automatically by Maya on startup
because it is located in the module's scripts/ folder.
"""

import maya.utils


def _setup_sbtools():
    import tris_to_quads_ui

    tris_to_quads_ui.build_menu()


# executeDeferred ensures the UI is fully loaded before building menus
maya.utils.executeDeferred(_setup_sbtools)
