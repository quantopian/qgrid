import ipywidgets as widgets
import pandas as pd
import json

from IPython.display import display
from numbers import Integral
from traitlets import Unicode, Instance, Bool, Integer, Dict, List, Tuple
import semver
if semver.compare(pd.__version__, '0.20.0') > 0:
    import pandas.io.json as pd_json
else:
    from . import pd_json


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
            'autoEdit': False,
            'explicitInitialization': True
        }
        self._show_toolbar = False
        self._remote_js = False
        self._precision = None  # Defer to pandas.get_option

    def set_grid_option(self, optname, optvalue):
        self._grid_options[optname] = optvalue

    def set_defaults(self, show_toolbar=None, remote_js=None,
                     precision=None, grid_options=None):
        if show_toolbar is not None:
            self._show_toolbar = show_toolbar
        if remote_js is not None:
            self._remote_js = remote_js
        if precision is not None:
            self._precision = precision
        if grid_options is not None:
            self._grid_options = grid_options

    @property
    def show_toolbar(self):
        return self._show_toolbar

    @property
    def grid_options(self):
        return self._grid_options

    @property
    def precision(self):
        return self._precision or pd.get_option('display.precision') - 1


defaults = _DefaultSettings()


def set_defaults(show_toolbar=None, precision=None, grid_options=None):
    """
    Set the default qgrid options.  The options that you can set here are the
    same ones that you can pass into ``QgridWidget`` constructor, with the
    exception of the ``df`` option, for which a default value wouldn't be
    particularly useful (since the purpose of qgrid is to display a DataFrame).

    See the documentation for ``QgridWidget`` for more information.

    Notes
    -----
    This function will be useful to you if you find yourself
    setting the same options every time you create a QgridWidget. Calling
    this ``set_defaults`` function once sets the options for the lifetime of
    the kernel, so you won't have to include the same options every time you
    instantiate a ``QgridWidget``.

    See Also
    --------
    QgridWidget :
        The widget whose default behavior is changed by ``set_defaults``.
    """
    defaults.set_defaults(show_toolbar, precision, grid_options)


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


def _display_as_qgrid(data):
    display(show_grid(data))


def enable(dataframe=True, series=True):
    """
    Automatically use qgrid to display all DataFrames and/or Series
    instances in the notebook.

    Parameters
    ----------
    dataframe : bool
        Whether to automatically use qgrid to display DataFrames instances.
    series : bool
        Whether to automatically use qgrid to display Series instances.
    """
    try:
        from IPython.core.getipython import get_ipython
    except ImportError:
        raise ImportError('This feature requires IPython 1.0+')

    ip = get_ipython()
    ip_formatter = ip.display_formatter.ipython_display_formatter

    if dataframe:
        ip_formatter.for_type(pd.DataFrame, _display_as_qgrid)
    else:
        ip_formatter.type_printers.pop(pd.DataFrame, None)

    if series:
        ip_formatter.for_type(pd.Series, _display_as_qgrid)
    else:
        ip_formatter.type_printers.pop(pd.Series)


def disable():
    """
    Stop using qgrid to display DataFrames and Series instances in the
    notebook.  This has the same effect as calling ``enable`` with both
    kwargs set to ``False`` (and in fact, that's what this function does
    internally).
    """
    enable(dataframe=False, series=False)


def show_grid(data_frame, show_toolbar=None,
              precision=None, grid_options=None):
    """
    Renders a DataFrame or Series as an interactive qgrid, represented by
    an instance of the ``QgridWidget`` class.  The ``QgridWidget`` instance
    is constructed using the options passed in to this function.  The
    ``data_frame`` argument to this function is used as the ``df`` kwarg in
    call to the QgridWidget constructor, and the rest of the parameters
    are passed through without any translation since they have the same name
    in the QgridWidget constructor.

    If the ``data_frame`` argument is a Series, it will be converted to a
    DataFrame before being passed in to the QgridWidget constructor as the
    ``df`` kwarg.

    See the ``QgridWidget`` documentation for descriptions of all of
    the options that can be set via it's constructor.

    :rtype: QgridWidget

    See Also
    --------
    QgridWidget : The widget class that is instantiated and returned by this
                  function.
    """

    if show_toolbar is None:
        show_toolbar = defaults.show_toolbar
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

    # if a Series is passed in, convert it to a DataFrame
    if isinstance(data_frame, pd.Series):
        data_frame = pd.DataFrame(data_frame)
    elif not isinstance(data_frame, pd.DataFrame):
        raise TypeError(
            "data_frame must be DataFrame or Series, not %s" % type(data_frame)
        )


    # create a visualization for the dataframe
    return QgridWidget(df=data_frame, precision=precision,
                       grid_options=grid_options,
                       show_toolbar=show_toolbar)

@widgets.register('qgrid.QgridWidget')
class QgridWidget(widgets.DOMWidget):
    """
    The widget class which is instantiated by the 'show_grid' method, and
    can also be constructed directly.  All of the parameters listed below
    can be read/updated after instantiation via attributes of the same name
    as the parameter (since they're implemented as traitlets).

    When new values are set for any of these options after instantiation
    (such as df, grid_options, etc), the change takes effect immediately by
    regenerating the SlickGrid control.

    Parameters
    ----------
    df : DataFrame
        The DataFrame that will be displayed by this instance of
        QgridWidget.
    grid_options : dict
        Options to use when creating the SlickGrid control (i.e. the
        interactive grid).  See the Notes section below for more information
        on the available options, as well as the default options that this
        widget uses.
    precision : integer
        The number of digits of precision to display for floating-point
        values.  If unset, we use the value of
        `pandas.get_option('display.precision')`.
    show_toolbar : bool
        Whether to show a toolbar with options for adding/removing rows.
        Adding/removing rows is an experimental feature which only works
        with DataFrames that have an integer index.

    Notes
    -----
    The following dictionary is used for ``grid_options`` if none are
    provided explicitly::

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

    See the `SlickGrid
    documentation
    <https://github.com/mleibman/SlickGrid/wiki/Grid-Options>`_
    for information about these options.

    See Also
    --------
    set_defaults : Permanently set global defaults for the parameters
                   of the QgridWidget constructor, with the exception of
                   the ``df`` parameter.
    set_grid_option : Permanently set global defaults for individual
                      SlickGrid options.  Does so by changing the default
                      for the ``grid_options`` parameter of the QgridWidget
                      constructor.

    Attributes
    ----------
    df : DataFrame
        Get/set the DataFrame that's being displayed by the current instance.
        This DataFrame will reflect any sorting/filtering/editing
        changes that are made via the UI.
    grid_options : dict
        Get/set the SlickGrid options being used by the current instance.
    precision : integer
        Get/set the precision options being used by the current instance.
    show_toolbar : bool
        Get/set the show_toolbar option being used by the current instance.

    """

    _view_name = Unicode('QgridView').tag(sync=True)
    _model_name = Unicode('QgridModel').tag(sync=True)
    _view_module = Unicode('qgrid').tag(sync=True)
    _model_module = Unicode('qgrid').tag(sync=True)
    _view_module_version = Unicode('1.0.0-alpha.6').tag(sync=True)
    _model_module_version = Unicode('1.0.0-alpha.6').tag(sync=True)

    _df_json = Unicode('', sync=True)
    _primary_key = List()
    _columns = Dict({}, sync=True)
    _filter_tables = Dict({})
    _sorted_column_cache = Dict({})
    _interval_columns = List([], sync=True)
    _index_name = Unicode('')
    _initialized = Bool(False)
    _ignore_df_changed = Bool(False)
    _unchanged_df = Instance(pd.DataFrame)
    _unfiltered_df = Instance(pd.DataFrame)
    _dirty = Bool(False)
    _multi_index = Bool(False)
    _edited = Bool(False)
    _selected_rows = List([])
    _page_size = Integer(100)
    _viewport_range = Tuple(Integer(), Integer(), default_value=(0, 100))
    _df_range = Tuple(Integer(), Integer(), default_value=(0, 100), sync=True)
    _row_count = Integer(0, sync=True)
    _sort_field = Unicode('', sync=True)
    _sort_ascending = Bool(True, sync=True)

    df = Instance(pd.DataFrame)
    precision = Integer(6, sync=True)
    grid_options = Dict(sync=True)
    show_toolbar = Bool(False, sync=True)

    def __init__(self, *args, **kwargs):
        self._initialized = False
        super(QgridWidget, self).__init__(*args, **kwargs)
        # register a callback for custom messages
        self.on_msg(self._handle_qgrid_msg)
        self._initialized = True
        if self.df is not None:
            self._update_df()

    def _grid_options_default(self):
        return defaults.grid_options

    def _precision_default(self):
        return defaults.precision

    def _update_df(self):
        self._ignore_df_changed = True
        self._unfiltered_df = self.df.copy()
        self._unchanged_df = self._unfiltered_df
        self._update_table(update_columns=True)
        self._ignore_df_changed = False

    def _rebuild_widget(self):
        self._update_df()
        self.send({'type': 'draw_table'})

    def _df_changed(self):
        """Build the Data Table for the DataFrame."""
        if self._ignore_df_changed or not self._initialized:
            return
        self._rebuild_widget()

    def _unchanged_df_changed(self):
        """Build the Data Table for the DataFrame."""
        if self._ignore_df_changed or not self._initialized:
            return
        self._ignore_df_changed = True
        self.df = self._unchanged_df
        self._rebuild_widget()
        self._ignore_df_changed = False

    def _precision_changed(self):
        self._rebuild_widget()

    def _grid_options_changed(self):
        self._rebuild_widget()

    def _show_toolbar_changed(self):
        self._rebuild_widget()

    def _update_table(self, update_columns=False, triggered_by=None):
        df = self.df.copy()

        from_index = max(self._viewport_range[0] - self._page_size, 0)
        to_index = max(self._viewport_range[0] + self._page_size, 0)
        self._df_range = (from_index, to_index)

        df = df.iloc[from_index:to_index]

        self._row_count = len(self.df.index)

        if type(df.index) == pd.core.index.MultiIndex:
            self._multi_index = True
        else:
            self._multi_index = False

        df_json = pd_json.to_json(None, df,
                            orient='table',
                            date_format='iso',
                            double_precision=self.precision)

        if update_columns:
            self._interval_columns = []
            parsed_json = json.loads(df_json)
            df_schema = parsed_json['schema']
            columns = {}
            for cur_column in df_schema['fields']:
                if 'constraints' in cur_column and isinstance(cur_column['constraints']['enum'][0], dict):
                    cur_column['type'] = 'interval'
                    self._interval_columns.append(cur_column['name'])
                columns[cur_column['name']] = cur_column

            self._primary_key = df_schema['primaryKey']
            self._columns = columns

        if len(self._interval_columns) > 0:
            df_for_display = df.copy()
            for col_name in self._interval_columns:
                df_for_display[col_name] = df[col_name].values.map(lambda x: str(x))
            df_json = pd_json.to_json(None, df_for_display,
                orient='table',
                date_format='iso',
                double_precision=self.precision
            )

        self._df_json = df_json

        if not update_columns:
            self.send({
                'type': 'update_data_view',
                'columns': self._columns,
                'triggered_by': triggered_by
            })

    def _initialize_df_backup(self):
        self._ignore_df_changed = True
        if self._unchanged_df is self._unfiltered_df:
            self._unchanged_df = self._unfiltered_df.copy()
        self._ignore_df_changed = False

    def _update_sort(self):
        if self._sort_field == '':
            return
        if self._sort_field in self._primary_key:
            if len(self._primary_key) == 1:
                self.df.sort_index(
                    ascending=self._sort_ascending,
                    inplace=True
                )
            else:
                self.df.sort_index(
                    level=self._sort_field,
                    ascending=self._sort_ascending,
                    inplace=True
                )
        else:
            self.df.sort_values(
                self._sort_field,
                ascending=self._sort_ascending,
                inplace=True
            )

    def _handle_get_column_min_max(self, content):
        col_name = content['field']
        col_info = self._columns[col_name]
        if 'filter_info' in col_info and 'selected' in col_info['filter_info']:
            df_for_unique = self._unfiltered_df
        else:
            df_for_unique = self.df


        if col_name in self._primary_key:
            if len(self._primary_key) > 1:
                key_index = self._primary_key.index(col_name)
                # col_series = df_for_unique.index.levels[key_index]
                get_val_from_level_index = \
                    lambda k: df_for_unique.index.levels[key_index][k]
                level_indices = df_for_unique.index.labels[key_index]
                level_series = pd.Series(level_indices)
                col_series = level_series.apply(get_val_from_level_index)
            else:
                col_series = df_for_unique.index
        else:
            col_series = df_for_unique[col_name]
        if col_info['type'] in ['integer', 'number']:
            if 'filter_info' not in col_info or \
                    (col_info['filter_info']['min'] is None and
                    col_info['filter_info']['max'] is None):
                col_info['slider_max'] = max(col_series)
                col_info['slider_min'] = min(col_series)
                self._columns[col_name] = col_info
            self.send({
                'type': 'column_min_max_updated',
                'field': col_name,
                'col_info': col_info
            })
            return
        elif col_info['type'] == 'datetime':
            if 'filter_info' not in col_info or \
                    (col_info['filter_info']['min'] is None and
                    col_info['filter_info']['max'] is None):
                col_info['filter_max'] = max(col_series)
                col_info['filter_min'] = min(col_series)
                self._columns[col_name] = col_info
            self.send({
                'type': 'column_min_max_updated',
                'field': col_name,
                'col_info': col_info
            })
            return
        elif col_info['type'] == 'boolean':
            self.log.info('handling boolean type')
            if 'filter_info' not in col_info:
                values = []
                for possible_val in [True, False]:
                    if possible_val in col_series:
                        values.append(possible_val)
                col_info['values'] = values
                self._columns[col_name] = col_info
            self.send({
                'type': 'column_min_max_updated',
                'field': col_name,
                'col_info': col_info
            })
            self.log.info('handled boolean type')
            return
        else:
            if col_info['type'] == 'any':
                unique_list = col_info['constraints']['enum']
            else:
                if col_name in self._sorted_column_cache:
                    unique_list = self._sorted_column_cache[col_name]
                else:
                    unique = col_series.unique()
                    if len(unique) < 500000:
                        unique.sort()
                    unique_list = unique.tolist()
                    self._sorted_column_cache[col_name] = unique_list

            if content['search_val'] is not None:
                unique_list = [
                    k for k in unique_list if content['search_val'].lower() in k.lower()
                ]

            if 'filter_info' in col_info and 'selected' in col_info['filter_info']:
                col_filter_info = col_info['filter_info']
                col_filter_table = self._filter_tables[col_name]
                get_value_from_filter_table = lambda k: col_filter_table[k]
                selected_indices = col_filter_info['selected'] or []
                if selected_indices == 'all':
                    excluded_indices = col_filter_info['excluded'] or []
                    excluded_values = list(map(get_value_from_filter_table, excluded_indices))
                    non_excluded_count = 0
                    for i in range(len(unique_list), 0, -1):
                        unique_val = unique_list[i-1]
                        if unique_val not in excluded_values:
                            non_excluded_count += 1
                            excluded_values.insert(0, unique_val)
                    col_info['values'] = excluded_values
                    col_info['selected_length'] = non_excluded_count
                elif len(selected_indices) == 0:
                    col_info['selected_length'] = 0
                    col_info['values'] = unique_list
                else:
                    selected_vals = list(map(get_value_from_filter_table, selected_indices))
                    col_info['selected_length'] = len(selected_vals)

                    in_selected = set(selected_vals)
                    in_unique = set(unique_list)

                    in_unique_but_not_selected = list(in_unique - in_selected)
                    in_unique_but_not_selected.sort()
                    selected_vals.extend(in_unique_but_not_selected)

                    col_info['values'] = selected_vals
            else:
                col_info['selected_length'] = 0
                col_info['values'] = unique_list


            length = len(col_info['values'])

            # only cache unique filter values if the
            # values are not filtered by a search string
            if content['search_val'] is None:
                self._filter_tables[col_name] = list(col_info['values'])

            if col_info['type'] == 'any':
                col_info['value_range'] = (0, length)
            else:
                max_items = self._page_size * 2
                range_max = length
                if length > max_items:
                    col_info['values'] = col_info['values'][:max_items]
                    range_max = max_items
                col_info['value_range'] = (0, range_max)

            col_info['length'] = length

            self._columns[col_name] = col_info

            if content['search_val'] is not None:
                self.send({
                    'type': 'update_data_view_filter',
                    'field': col_name,
                    'col_info': col_info
                })
            else:
                self.send({
                    'type': 'column_min_max_updated',
                    'field': col_name,
                    'col_info': col_info
                })

    def _handle_filter_changed(self, content):
        col_name = content['field']
        columns = self._columns.copy()
        col_info = columns[col_name]
        col_info['filter_info'] = content['filter_info']
        columns[col_name] = col_info

        conditions = []
        for key, value in columns.items():
            if 'filter_info' in value:
                if key in self._primary_key:
                    if len(self._primary_key) > 1:
                        key_index = self._primary_key.index(key)
                        get_value_from_df = lambda df: df.index.get_level_values(level=key_index)
                    else:
                        get_value_from_df = lambda df: df.index
                else:
                    get_value_from_df = lambda df: df[key]

                filter_info = value['filter_info']
                if filter_info['type'] == 'slider':
                    if filter_info['min'] is not None:
                        conditions.append(get_value_from_df(self._unfiltered_df) >= filter_info['min'])
                    if filter_info['max'] is not None:
                        conditions.append(get_value_from_df(self._unfiltered_df) <= filter_info['max'])
                elif filter_info['type'] == 'date':
                    if filter_info['min'] is not None:
                        conditions.append(get_value_from_df(self._unfiltered_df) >= pd.to_datetime(filter_info['min'], unit='ms'))
                    if filter_info['max'] is not None:
                        conditions.append(get_value_from_df(self._unfiltered_df) <= pd.to_datetime(filter_info['max'], unit='ms'))
                elif filter_info['type'] == 'boolean':
                    if filter_info['selected'] is not None:
                        conditions.append(get_value_from_df(self._unfiltered_df) == filter_info['selected'])
                elif filter_info['type'] == 'text':
                    if key not in self._filter_tables:
                        continue
                    col_filter_table = self._filter_tables[key]
                    selected_indices = filter_info['selected']
                    excluded_indices = filter_info['excluded']
                    get_value_from_filter_table = lambda i: col_filter_table[i]
                    if selected_indices == "all":
                        if excluded_indices is not None and len(excluded_indices) > 0:
                            excluded_values = list(map(get_value_from_filter_table, excluded_indices))
                            conditions.append(~get_value_from_df(self._unfiltered_df).isin(excluded_values))
                    elif selected_indices is not None and len(selected_indices) > 0:
                        selected_values = list(map(get_value_from_filter_table, selected_indices))
                        conditions.append(get_value_from_df(self._unfiltered_df).isin(selected_values))

        self._columns = columns

        self._ignore_df_changed = True
        if len(conditions) == 0:
            self.df = self._unfiltered_df.copy()
        else:
            combined_condition = conditions[0]
            for c in conditions[1:]:
                combined_condition = combined_condition & c

            self.df = self._unfiltered_df[combined_condition].copy()

        self._sorted_column_cache = {}
        self._update_sort()
        self._update_table(triggered_by='filter_changed')
        self._ignore_df_changed = False

    def _handle_qgrid_msg(self, widget, content, buffers=None):
        try:
            self._handle_qgrid_msg_helper(content)
        except Exception as e:
            self.log.error(e)
            self.log.exception("Unhandled exception while handling msg")

    def _handle_qgrid_msg_helper(self, content):
        """Handle incoming messages from the QGridView"""
        if 'type' not in content:
            return

        if content['type'] == 'cell_change':
            try:
                self.df.set_value(self.df.index[content['row']],
                                  content['column'], content['value'])
                self._dirty = True
            except ValueError:
                pass
        elif content['type'] == 'selection_change':
            self._selected_rows = content['rows']
        elif content['type'] == 'viewport_changed':
            self._viewport_range = (content['top'], content['bottom'])
            self._update_table()
        elif content['type'] == 'add_row':
            self.add_row()
        elif content['type'] == 'remove_row':
            self.remove_row()
        elif content['type'] == 'viewport_changed_filter':
            col_name = content['field']
            col_info = self._columns[col_name]
            col_filter_table = self._filter_tables[col_name]

            from_index = max(content['top'] - self._page_size, 0)
            to_index = max(content['top'] + self._page_size, 0)

            col_info['values'] = col_filter_table[from_index:to_index]
            col_info['value_range'] = (from_index, to_index)
            self._columns[col_name] = col_info
            self.send({
                'type': 'update_data_view_filter',
                'field': col_name,
                'col_info': col_info
            })
        elif content['type'] == 'sort_changed':
            self._sort_field = content['sort_field']
            self._sort_ascending = content['sort_ascending']
            self._sorted_column_cache = {}
            self._update_sort()
            self._update_table()
        elif content['type'] == 'get_column_min_max':
            self._handle_get_column_min_max(content)
        elif content['type'] == 'filter_changed':
            self._handle_filter_changed(content)

    def get_unchanged_df(self):
        return self._unchanged_df

    def get_selected_rows(self):
        """Get the currently selected rows"""
        return self._selected_rows

    def add_row(self):
        """Append a row at the end of the dataframe by duplicating the
        last row and incrementing it's index by 1. The feature is only
        available for DataFrames that have an integer index."""
        df = self.df

        if not df.index.is_integer():
            msg = "Cannot add a row to a table with a non-integer index"
            self.send({
                'type': 'show_error',
                'error_msg': msg,
                'triggered_by': 'add_row'
            })
            return
        self._initialize_df_backup()
        last = df.iloc[-1]
        last.name += 1
        df.loc[last.name] = last.values
        self._unfiltered_df.loc[last.name] = last.values
        self._update_table(triggered_by='add_row')

    def remove_row(self):
        """Remove the current row from the table"""
        if self._multi_index:
            msg = "Cannot remove a row from a table with a multi index"
            self.send({
                'type': 'show_error',
                'error_msg': msg,
                'triggered_by': 'remove_row'
            })
            return
        self._initialize_df_backup()
        selected_names = \
            map(lambda x: self.df.iloc[x].name, self._selected_rows)
        self.df.drop(selected_names, inplace=True)
        self._unfiltered_df.drop(selected_names, inplace=True)
        self._selected_rows = []
        self._update_table(triggered_by='remove_row')

# Alias for legacy support, since we changed the capitalization
QGridWidget = QgridWidget
