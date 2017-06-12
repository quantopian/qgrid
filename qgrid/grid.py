import pandas as pd
import numpy as np
import uuid
import os
import json
from numbers import Integral

from IPython.display import display_html, display_javascript
try:
    from ipywidgets import widgets
except ImportError:
    from IPython.html import widgets
from IPython.display import display, Javascript
try:
    from traitlets import Unicode, Instance, Bool, Integer, Dict, List
except ImportError:
    from IPython.utils.traitlets import (
        Unicode, Instance, Bool, Integer, Dict, List
    )


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
REMOTE_URL = ("https://cdn.rawgit.com/quantopian/qgrid/"
              "73eaa7adf1762f66eaf4d30ed9cbf385a7e9d9fa/qgrid/qgridjs/")
LOCAL_URL = "/nbextensions/qgridjs"


class _DefaultSettings(object):

    def __init__(self):
        self._grid_options = {
            'fullWidthRows': True,
            'syncColumnCellResize': True,
            'forceFitColumns': True,
            'defaultColumnWidth': 150,
            'rowHeight': 28,
            'enableColumnReorder': False,
            'enableTextSelectionOnCells': True,
            'editable': True,
            'autoEdit': False
        }
        self._show_toolbar = False
        self._export_mode = False
        self._remote_js = False
        self._precision = None  # Defer to pandas.get_option

    def set_grid_option(self, optname, optvalue):
        self._grid_options[optname] = optvalue

    def set_defaults(self, show_toolbar=None, remote_js=None, precision=None, grid_options=None, export_mode=None):
        if show_toolbar is not None:
            self._show_toolbar = show_toolbar
        if remote_js is not None:
            self._remote_js = remote_js
        if precision is not None:
            self._precision = precision
        if grid_options is not None:
            self._grid_options = grid_options
        if export_mode is not None:
            self._export_mode = export_mode

    @property
    def show_toolbar(self):
        return self._show_toolbar

    @property
    def export_mode(self):
        return self._export_mode

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


def set_defaults(show_toolbar=None, remote_js=None, precision=None, grid_options=None, export_mode=None):
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
    defaults.set_defaults(show_toolbar, remote_js, precision, grid_options, export_mode)


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
    defaults.grid_options[optname] = optvalue


def show_grid(data_frame, show_toolbar=None, remote_js=None, precision=None, grid_options=None, export_mode=None):
    """
    Main entry point for rendering DataFrames as SlickGrids.

    Parameters
    ----------
    grid_options : dict
        Options to use when creating javascript SlickGrid instances.  See the Notes section below for
        more information on the available options, as well as the default options that qgrid uses.
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
    show_toolbar : bool
        Whether to show a toolbar with options for adding/removing rows and
        exporting the widget to a static view.  Adding/removing rows is an
        experimental feature which only works with DataFrames that have an
        integer index.  The export feature is used to generate a copy of the
        grid that will be mostly functional when rendered in nbviewer.jupyter.org
        or when exported to html via the notebook's File menu.
    export_mode : bool
        Whether to display the grid in a notebook or to prepare it to be exported

    Notes
    -----
    By default, the following options get passed into SlickGrid when
    ``show_grid`` is called.  See the `SlickGrid documentation
    <https://github.com/mleibman/SlickGrid/wiki/Grid-Options>`_ for information
    about these options::

        {
            'fullWidthRows': True,
            'syncColumnCellResize': True,
            'forceFitColumns': True,
            'rowHeight': 28,
            'enableColumnReorder': False,
            'enableTextSelectionOnCells': True,
            'editable': True,
            'autoEdit': False
        }

    See Also
    --------
    set_defaults : Permanently set global defaults for `show_grid`.
    set_grid_option : Permanently set individual SlickGrid options.
    """

    if show_toolbar is None:
        show_toolbar = defaults.show_toolbar
    if export_mode is None:
        export_mode = defaults.export_mode
    if remote_js is None:
        remote_js = defaults.remote_js
    if precision is None:
        precision = defaults.precision
    if not isinstance(precision, Integral):
        raise TypeError("precision must be int, not %s" % type(precision))
    if grid_options is None:
        grid_options = defaults.grid_options
    else:
        options = defaults.grid_options.copy()
        options.update(grid_options)
        grid_options = options
    if not isinstance(grid_options, dict):
        raise TypeError(
            "grid_options must be dict, not %s" % type(grid_options)
        )

    # create a visualization for the dataframe
    grid = QGridWidget(df=data_frame, precision=precision,
                       grid_options=grid_options,
                       remote_js=remote_js)

    if show_toolbar:
        add_row = widgets.Button(description="Add Row")
        add_row.on_click(grid.add_row)

        rem_row = widgets.Button(description="Remove Row")
        rem_row.on_click(grid.remove_row)

        export = widgets.Button(description="Export")
        export.on_click(grid.export)

        return widgets.VBox([widgets.HBox([add_row, rem_row, export]), grid])
    else:
        if export_mode:
            grid.export()
            return None
        else:
            return grid

class QGridWidget(widgets.DOMWidget):
    _view_module = Unicode("nbextensions/qgridjs/qgrid.widget", sync=True)
    _view_name = Unicode('QGridView', sync=True)
    _df_json = Unicode('', sync=True)
    _column_types_json = Unicode('', sync=True)
    _index_name = Unicode('')
    _initialized = Bool(False)
    _dirty = Bool(False)
    _cdn_base_url = Unicode(LOCAL_URL, sync=True)
    _multi_index = Bool(False)
    _selected_rows = List()

    df = Instance(pd.DataFrame)
    precision = Integer(6)
    grid_options = Dict(sync=True)
    remote_js = Bool(False)

    def __init__(self, *args, **kwargs):
        """Initialize all variables before building the table."""
        self._initialized = False
        super(QGridWidget, self).__init__(*args, **kwargs)
        # register a callback for custom messages
        self.on_msg(self._handle_qgrid_msg)
        self._initialized = True
        self._selected_rows = []
        if self.df is not None:
            self._update_table()

    def _grid_options_default(self):
        return defaults.grid_options

    def _remote_js_default(self):
        return defaults.remote_js

    def _precision_default(self):
        return defaults.precision

    def _df_changed(self):
        """Build the Data Table for the DataFrame."""
        if not self._initialized:
            return
        self._update_table()
        self.send({'type': 'draw_table'})

    def _update_table(self):
        df = self.df.copy()

        if not df.index.name:
            df.index.name = 'Index'

        if type(df.index) == pd.core.index.MultiIndex:
            df.reset_index(inplace=True)
            self._multi_index = True
        else:
            df.insert(0, df.index.name, df.index)
            self._multi_index = False

        self._index_name = df.index.name or 'Index'

        tc = dict(np.typecodes)
        for key in np.typecodes.keys():
            if "All" in key:
                del tc[key]

        column_types = []
        for col_name, dtype in df.dtypes.iteritems():
            if str(dtype) == 'category':
                categories = list(df[col_name].cat.categories)
                column_type = {'field': col_name,
                               'categories': ','.join(categories)}
                # XXXX: work around bug in to_json for categorical types
                # https://github.com/pydata/pandas/issues/10778
                df[col_name] = df[col_name].astype(str)
                column_types.append(column_type)
                continue
            column_type = {'field': col_name}
            for type_name, type_codes in tc.items():
                if dtype.kind in type_codes:
                    column_type['type'] = type_name
                    break
            column_types.append(column_type)
        self._column_types_json = json.dumps(column_types)

        self._df_json = df.to_json(
                orient='records',
                date_format='iso',
                double_precision=self.precision,
            )
        self._cdn_base_url = REMOTE_URL if self.remote_js else LOCAL_URL
        self._dirty = False

    def add_row(self, value=None):
        """Append a row at the end of the dataframe."""
        df = self.df
        if not df.index.is_integer():
            msg = "Cannot add a row to a table with a non-integer index"
            display(Javascript('alert("%s")' % msg))
            return
        last = df.iloc[-1]
        last.name += 1
        df.loc[last.name] = last.values
        precision = pd.get_option('display.precision') - 1
        row_data = last.to_json(date_format='iso',
                                double_precision=precision)
        msg = json.loads(row_data)
        msg[self._index_name] = str(last.name)
        msg['slick_grid_id'] = str(last.name)
        msg['type'] = 'add_row'
        self._dirty = True
        self.send(msg)

    def remove_row(self, value=None):
        """Remove the current row from the table"""
        if self._multi_index:
            msg = "Cannot remove a row from a table with a multi index"
            display(Javascript('alert("%s")' % msg))
            return
        self.send({'type': 'remove_row'})

    def _handle_qgrid_msg(self, widget, content, buffers=None):
        """Handle incoming messages from the QGridView"""
        if 'type' not in content:
            return
        if content['type'] == 'remove_row':
            self.df.drop(content['row'], inplace=True)
            self._dirty = True

        elif content['type'] == 'cell_change':
            try:
                self.df.set_value(self.df.index[content['row']],
                                  content['column'], content['value'])
                self._dirty = True
            except ValueError:
                pass

        elif content['type'] == 'selection_change':
            self._selected_rows = content['rows']

    def get_selected_rows(self):
        """Get the currently selected rows"""
        return self._selected_rows

    def export(self, value=None):
        if self._dirty:
            self._update_table()
        base_url = REMOTE_URL
        div_id = str(uuid.uuid4())
        grid_options = self.grid_options
        grid_options['editable'] = False

        raw_html = SLICK_GRID_CSS.format(
            div_id=div_id,
            cdn_base_url=base_url,
        )
        raw_js = SLICK_GRID_JS.format(
            cdn_base_url=base_url,
            div_id=div_id,
            data_frame_json=self._df_json,
            column_types_json=self._column_types_json,
            options_json=json.dumps(grid_options),
        )

        display_html(raw_html, raw=True)
        display_javascript(raw_js, raw=True)
