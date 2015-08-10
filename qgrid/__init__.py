from .grid import (
    set_defaults,
    set_grid_option,
    show_grid,
)
from .grid import QGridWidget
import os

QGRIDJS_PATH = os.path.join(
        os.path.dirname(__file__),
        'qgridjs',
    )


def edit_grid(data_frame, auto_edit=False, remote_js=False):
    # Lazy imports so we don't pollute the namespace.
    from IPython.html.widgets import Button, HBox
    from IPython.display import display

    # create a visualization for the dataframe
    grid = QGridWidget(df=data_frame, auto_edit=auto_edit, remote_js=remote_js)

    add_row = Button(description="Add Row")
    add_row.on_click(grid.add_row)

    rem_row = Button(description="Remove Row")
    rem_row.on_click(grid.remove_row)

    display(HBox((add_row, rem_row)), grid)

    return grid


def nbinstall(user=True, overwrite=False):
    """
    """
    # Lazy imports so we don't pollute the namespace.
    from IPython.html.nbextensions import install_nbextension
    from IPython.html.services.config import ConfigManager
    from IPython import version_info
    from IPython.display import display, Javascript

    install_nbextension(
        QGRIDJS_PATH,
        overwrite=overwrite,
        symlink=False,
        verbose=0,
        **({'user': user} if version_info>=(3, 0, 0, '') else {})
    )
    cm = ConfigManager()
    cm.update('notebook', {"load_extensions": {"qgridjs/qgrid.widget": True}})

    display(Javascript("IPython.load_extensions('qgridjs/qgrid.widget');"))


__all__ = ['show_grid', 'set_defaults', 'set_grid_option', 'edit_grid']
