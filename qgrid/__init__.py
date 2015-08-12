from .grid import (
    set_defaults,
    set_grid_option,
    show_grid,
    edit_grid
)


def nbinstall(user=True, overwrite=False):
    """
    """
    # Lazy imports so we don't pollute the namespace.
    import os
    from IPython.html.nbextensions import install_nbextension
    from IPython.html.services.config import ConfigManager
    from IPython import version_info
    from IPython.display import display, Javascript

    qgridjs_path = os.path.join(
        os.path.dirname(__file__),
        'qgridjs',
    )

    install_nbextension(
        qgridjs_path,
        overwrite=overwrite,
        symlink=False,
        verbose=0,
        **({'user': user} if version_info>=(3, 0, 0, '') else {})
    )
    cm = ConfigManager()
    cm.update('notebook', {"load_extensions": {"qgridjs/qgrid.widget": True}})

    display(Javascript("IPython.load_extensions('qgridjs/qgrid.widget');"))


__all__ = ['show_grid', 'set_defaults', 'set_grid_option', 'edit_grid']
