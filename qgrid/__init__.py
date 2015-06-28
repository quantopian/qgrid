from .grid import (
    set_defaults,
    set_js_option,
    show_grid,
)


def nbinstall(user=True, overwrite=False):
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
        user=user,
        symlink=False,
        verbose=0,
    )


__all__ = ['show_grid', 'set_defaults', 'set_js_option']
