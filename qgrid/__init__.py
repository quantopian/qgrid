from .grid import SlickGrid


def show_grid(data_frame):
    return SlickGrid(data_frame)


def set_remote_mode(remote_mode=True):
    SlickGrid.remote_mode = remote_mode


def nbinstall(overwrite=False):
    """
    """
    # Lazy imports so we don't pollute the namespace.
    import os
    from IPython.html.nbextensions import install_nbextension

    qgridjs_path = os.path.join(
        os.path.dirname(__file__),
        'qgridjs',
    )

    install_nbextension(
        qgridjs_path,
        overwrite=overwrite,
        symlink=False,
        verbose=0,
    )
