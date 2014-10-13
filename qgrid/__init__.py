from .grid import SlickGrid


def show_grid(data_frame, remote_js=False):
    return SlickGrid(data_frame, remote_js)


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


def monkey_patch(pandas, remote_js=False):
    "Make qgrid the default display method for DataFrames."

    def _ipython_display_(self):
        return show_grid(self, remote_js=remote_js)._ipython_display_()

    pandas.DataFrame._ipython_display_ = _ipython_display_
