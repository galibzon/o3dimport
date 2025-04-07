"""
Copyright (c) Contributors to the Open 3D Engine Project.
For complete copyright and license terms please see the LICENSE at the root of this distribution.

SPDX-License-Identifier: Apache-2.0 OR MIT
"""
# -------------------------------------------------------------------------
"""o3dimport\\editor\\scripts\\boostrap.py
Generated from O3DE PythonToolGem Template"""

import az_qt_helpers
from o3dimport_dialog import o3dimportDialog

if __name__ == "__main__":
    print("o3dimport.boostrap, Generated from O3DE PythonToolGem Template")

    try:
        import azlmbr.editor as editor
        # Register our custom widget as a dockable tool with the Editor under an Examples sub-menu
        options = editor.ViewPaneOptions()
        options.showOnToolsToolbar = True
        options.toolbarIcon = ":/o3dimport/toolbar_icon.svg"
        az_qt_helpers.register_view_pane('o3dimport', o3dimportDialog, category="Examples", options=options)
    except:
        # If the editor is not available (in the cases where this gem is activated outside of the Editor), then just 
        # report it and continue.
        print(f'Skipping registering view pane o3dimport, Editor is not available.')
