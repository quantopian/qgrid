from .grid import SlickGrid


def show_grid(data_frame, remote_js=False):
    return SlickGrid(data_frame, remote_js)


def nbinstall(user=True, overwrite=False):
    """
    """
    # Lazy imports so we don't pollute the namespace.
    import os
    from IPython.html.nbextensions import install_nbextension
    from IPython import version_info

    qgridjs_path = os.path.join(
        os.path.dirname(__file__),
        'qgridjs',
    )

    if version_info >= (3, 0, 0, ''):
        install_nbextension(
            qgridjs_path,
            overwrite=overwrite,
            user=user,
            symlink=False,
            verbose=0,
        )
    elif version_info >= (2, 0, 0, ''):
        # Leave out the user argument with IPython 2.x series
        install_nbextension(
            qgridjs_path,
            overwrite=overwrite,
            symlink=False,
            verbose=0,
        )
    else:
        raise NotImplementedError("Only supported for IPython>=2.0.")
