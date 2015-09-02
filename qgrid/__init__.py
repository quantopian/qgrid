from .grid import (
    set_defaults,
    set_grid_option,
    show_grid,
)


def nbinstall(overwrite=False, user=True):
    """
    Copies javascript and css dependencies to the '/nbextensions' folder in
    your IPython directory.

    Parameters
    ----------

    overwrite : bool
        If True, always install the files, regardless of what may already be
        installed.  Defaults to False.
    user : bool
        Whether to install to the user's .ipython/nbextensions directory.
        Otherwise do a system-wide install
        (e.g. /usr/local/share/jupyter/nbextensions).  Defaults to False.

    Notes
    -----
    After you install qgrid, call this function once before attempting to
    call ``show_grid``.
    """

    # Lazy imports so we don't pollute the namespace.
    import os
    from IPython.html.nbextensions import install_nbextension
    from IPython import version_info

    qgridjs_path = os.path.join(
        os.path.dirname(__file__),
        'qgridjs',
    )

    install_nbextension(
        qgridjs_path,
        overwrite=overwrite,
        symlink=False,
        verbose=0,
        **({'user': user} if version_info >= (3, 0, 0, '') else {})
    )


__all__ = ['nbinstall', 'show_grid', 'set_defaults', 'set_grid_option']
