import pandas as pd
import numpy as np
import os
import uuid
import json
from numbers import Integral

from IPython.display import display_html, display_javascript


def template_contents(filename):
    template_filepath = os.path.join(
        os.path.dirname(__file__),
        'templates',
        filename,
    )
    with open(template_filepath) as f:
        return f.read()


SLICK_GRID_CSS = template_contents('slickgrid.css.template')
SLICK_GRID_JS = template_contents('slickgrid.js.template')


class _DefaultSettings(object):

    def __init__(self):
        self._grid_options = {
            'fullWidthRows': True,
            'syncColumnCellResize': True,
            'forceFitColumns': True,
            'rowHeight': 28,
            'enableColumnReorder': False,
            'enableTextSelectionOnCells': True,
        }
        self._remote_js = False
        self._precision = None  # Defer to pandas.get_option

    def set_grid_option(self, optname, optvalue):
        self._grid_options[optname] = optvalue

    def set_defaults(self, remote_js=None, precision=None, grid_options=None):
        if remote_js is not None:
            self._remote_js = remote_js
        if precision is not None:
            self._precision = precision
        if grid_options is not None:
            self._grid_options = grid_options

    @property
    def grid_options(self):
        return self._grid_options

    @property
    def remote_js(self):
        return self._remote_js

    @property
    def precision(self):
        return self._precision or pd.get_option('display.precision') - 1

defaults = _DefaultSettings()

def set_defaults(remote_js=None, precision=None, grid_options=None):
    """
    Set the default qgrid options.  The options that you can set here are the
    same ones that you can pass into ``show_grid``.  See the documentation
    for ``show_grid`` for more information.

    Notes
    -----
    This function will be useful to you if you find yourself
    setting the same options every time you make a call to ``show_grid``.
    Calling this ``set_defaults`` function once sets the options for the
    lifetime of the kernel, so you won't have to include the same options
    every time you call ``show_grid``.

    See Also
    --------
    show_grid :
        The function whose default behavior is changed by ``set_defaults``.
    """
    defaults.set_defaults(remote_js, precision, grid_options)


def set_grid_option(optname, optvalue):
    """
    Set the default value for one of the options that gets passed into the
    SlickGrid constructor.

    Parameters
    ----------
    optname : str
        The name of the option to set.
    optvalue : object
        The new value to set.

    Notes
    -----
    The options you can set here are the same ones
    that you can set via the ``grid_options`` parameter of the ``set_defaults``
    or ``show_grid`` functions.  See the `SlickGrid documentation
    <https://github.com/mleibman/SlickGrid/wiki/Grid-Options>`_ for the full
    list of available options.
    """
def show_grid(data_frame, remote_js=None, precision=None, grid_options=None):
    """
    Main entry point for rendering DataFrames as SlickGrids.

    Parameters
    ----------
    remote_js : bool
        Whether to load slickgrid.js from a local filesystem or from a
        remote CDN.  Loading from the local filesystem means that SlickGrid
        will function even when not connected to the internet, but grid
        cells created with local filesystem loading will not render
        correctly on external sharing services like NBViewer.
    precision : integer
        The number of digits of precision to display for floating-point
        values.  If unset, we use the value of
        `pandas.get_option('display.precision')`.
    grid_options : dict
        Options to use when creating javascript SlickGrid instances.  See
        the `SlickGrid documentation <https://github.com/mleibman/SlickGrid/wiki/Grid-Options>`_ for
        information on the available options.  See the Notes section below for
        the list of options that qgrid sets by default.

    Notes
    -----
    By default, the following options get passed into SlickGrid when
    ``show_grid`` is called.  See the `SlickGrid documentation
    <https://github.com/mleibman/SlickGrid/wiki/Grid-Options>`_ for information
    about these options.
    ::
        {
            'fullWidthRows': True,
            'syncColumnCellResize': True,
            'forceFitColumns': True,
            'rowHeight': 28,
            'enableColumnReorder': False,
            'enableTextSelectionOnCells': True,
        }


    See Also
    --------
    set_defaults : Permanently set global defaults for `show_grid`.
    set_grid_option : Permanently set individual SlickGrid options.
    """

    if remote_js is None:
        remote_js = defaults.remote_js
    if precision is None:
        precision = defaults.precision
        if not isinstance(precision, Integral):
            raise TypeError("precision must be int, not %s" % type(precision))
    if grid_options is None:
        grid_options = defaults.grid_options
        if not isinstance(grid_options, dict):
            raise TypeError(
                "grid_options must be dict, not %s" % type(grid_options)
            )

    return SlickGrid(
        data_frame,
        remote_js=remote_js,
        precision=precision,
        grid_options=grid_options,
    )


class SlickGrid(object):

    def __init__(self, data_frame, remote_js, precision, grid_options):
        self.data_frame = data_frame
        self.remote_js = remote_js
        self.div_id = str(uuid.uuid4())

        self.df_copy = data_frame.copy()

        if type(self.df_copy.index) == pd.core.index.MultiIndex:
            self.df_copy.reset_index(inplace=True)
        else:
            self.df_copy.insert(0, self.df_copy.index.name, self.df_copy.index)

        tc = dict(np.typecodes)
        for key in np.typecodes.keys():
            if "All" in key:
                del tc[key]

        self.column_types = []
        for col_name, dtype in self.df_copy.dtypes.iteritems():
            column_type = {'field': col_name}
            for type_name, type_codes in tc.items():
                if dtype.kind in type_codes:
                    column_type['type'] = type_name
                    break
            self.column_types.append(column_type)

        self.precision = precision
        self.grid_options = grid_options

    def _ipython_display_(self):
        try:
            column_types_json = json.dumps(self.column_types)
            data_frame_json = self.df_copy.to_json(
                orient='records',
                date_format='iso',
                double_precision=self.precision,
            )
            options_json = json.dumps(self.grid_options)

            if self.remote_js:
                cdn_base_url = \
                    "https://cdn.rawgit.com/quantopian/qgrid/72d356cb123fab413dba73ec46616e4916fbd827/qgrid/qgridjs/"
            else:
                cdn_base_url = "/nbextensions/qgridjs"

            raw_html = SLICK_GRID_CSS.format(
                div_id=self.div_id,
                cdn_base_url=cdn_base_url,
            )
            raw_js = SLICK_GRID_JS.format(
                cdn_base_url=cdn_base_url,
                div_id=self.div_id,
                data_frame_json=data_frame_json,
                column_types_json=column_types_json,
                options_json=options_json,
            )

            display_html(raw_html, raw=True)
            display_javascript(raw_js, raw=True)
        except Exception as err:
            display_html('ERROR: {}'.format(str(err)), raw=True)
