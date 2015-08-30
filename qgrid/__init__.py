from .grid import (
    set_defaults,
    set_grid_option,
    show_grid
)


def nbinstall(user=True, overwrite=False):
    """
    """
    # Lazy imports so we don't pollute the namespace.
    import os
    try:
        from notebook import install_nbextension
        from notebook.services.config import ConfigManager
    except ImportError:
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

    with open(os.path.join(qgridjs_path, 'qgrid.widget.js')) as fid:
        display(Javascript(fid.read()))


__all__ = ['set_defaults', 'set_grid_option', 'show_grid']
