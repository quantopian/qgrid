import ipywidgets as widgets
import pandas as pd
import numpy as np
import json

from IPython.display import display
from numbers import Integral
from traitlets import Unicode, Instance, Bool, Integer, Dict, List, Tuple, Any

# versions of pandas prior to version 0.20.0 don't support the orient='table'
# when calling the 'to_json' function on DataFrames.  to get around this we
# have our own copy of the panda's 0.20.0 implementation that we use for old
# versions of pandas.
from distutils.version import LooseVersion
if LooseVersion(pd.__version__) > LooseVersion('0.20.0'):
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
            'explicitInitialization': True,
            'maxVisibleRows': 15,
            'minVisibleRows': 8
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
    are passed through as is.

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


@widgets.register()
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
        This DataFrame will NOT reflect any sorting/filtering/editing
        changes that are made via the UI. To get a copy of the DataFrame that
        does reflect sorting/filtering/editing changes, use the
        ``get_changed_df()`` method.
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
    _view_module_version = Unicode('1.0.0-beta.9').tag(sync=True)
    _model_module_version = Unicode('1.0.0-beta.9').tag(sync=True)

    _df = Instance(pd.DataFrame)
    _df_json = Unicode('', sync=True)
    _page_size = Integer(100, sync=True)
    _primary_key = List()
    _columns = Dict({}, sync=True)
    _filter_tables = Dict({})
    _sorted_column_cache = Dict({})
    _interval_columns = List([], sync=True)
    _period_columns = List([])
    _string_columns = List([])
    _sort_helper_columns = Dict({})
    _initialized = Bool(False)
    _ignore_df_changed = Bool(False)
    _unfiltered_df = Instance(pd.DataFrame)
    _index_col_name = Unicode('qgrid_unfiltered_index', sync=True)
    _sort_col_suffix = Unicode('_qgrid_sort_column')
    _multi_index = Bool(False)
    _edited = Bool(False)
    _selected_rows = List([])
    _viewport_range = Tuple(Integer(), Integer(), default_value=(0, 100))
    _df_range = Tuple(Integer(), Integer(), default_value=(0, 100), sync=True)
    _row_count = Integer(0, sync=True)
    _sort_field = Any('', sync=True)
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
        # make a copy of the user's dataframe
        self._df = self.df.copy()

        # insert a column which we'll use later to map edits from
        # a filtered version of this df back to the unfiltered version
        self._df.insert(0, self._index_col_name, range(0, len(self._df)))

        # keep an unfiltered version to serve as the starting point
        # for filters, and the state we return to when filters are removed
        self._unfiltered_df = self._df.copy()

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

    def _precision_changed(self):
        if not self._initialized:
            return
        self._rebuild_widget()

    def _grid_options_changed(self):
        if not self._initialized:
            return
        self._rebuild_widget()

    def _show_toolbar_changed(self):
        if not self._initialized:
            return
        self._rebuild_widget()

    def _update_table(self, update_columns=False, triggered_by=None,
                      scroll_to_row=None):
        df = self._df.copy()

        from_index = max(self._viewport_range[0] - self._page_size, 0)
        to_index = max(self._viewport_range[0] + self._page_size, 0)
        new_df_range = (from_index, to_index)

        if triggered_by is 'viewport_changed' and \
                self._df_range == new_df_range:
            return

        self._df_range = new_df_range

        df = df.iloc[from_index:to_index]

        self._row_count = len(self._df.index)

        if type(df.index) == pd.core.index.MultiIndex:
            self._multi_index = True
        else:
            self._multi_index = False

        if update_columns:
            self._string_columns = list(df.select_dtypes(
                include=[np.dtype('O')]
            ).columns.values)

        # call map(str) for all columns identified as string columns, in
        # case any are not strings already
        for col_name in self._string_columns:
            sort_column_name = self._sort_helper_columns.get(col_name)
            if sort_column_name:
                series_to_set = df[sort_column_name]
            else:
                series_to_set = self._get_col_series_from_df(
                    col_name, df
                ).map(str)
            self._set_col_series_on_df(col_name, df, series_to_set)

        df_json = pd_json.to_json(None, df,
                                  orient='table',
                                  date_format='iso',
                                  double_precision=self.precision)

        if update_columns:
            self._interval_columns = []
            self._sort_helper_columns = {}
            self._period_columns = []

            # parse the schema that we just exported in order to get the
            # column metadata that was generated by 'to_json'
            parsed_json = json.loads(df_json)
            df_schema = parsed_json['schema']

            if ('primaryKey' in df_schema):
                self._primary_key = df_schema['primaryKey']
            else:
                # for some reason, 'primaryKey' isn't set when the index is
                # a single interval column. that's why this case is here.
                self._primary_key = [df.index.name]

            columns = {}
            for i, cur_column in enumerate(df_schema['fields']):
                col_name = cur_column['name']
                if 'constraints' in cur_column and \
                        isinstance(cur_column['constraints']['enum'][0], dict):
                    cur_column['type'] = 'interval'
                    self._interval_columns.append(col_name)

                if 'freq' in cur_column:
                    self._period_columns.append(col_name)

                if col_name in self._primary_key:
                    cur_column['is_index'] = True

                cur_column['position'] = i
                columns[col_name] = cur_column

            self._columns = columns

        # special handling for interval columns: convert to a string column
        # and then call 'to_json' again to get a new version of the table
        # json that has interval columns replaced with text columns
        if len(self._interval_columns) > 0:
            for col_name in self._interval_columns:
                col_series = self._get_col_series_from_df(col_name, df)
                col_series_as_strings = col_series.map(lambda x: str(x))
                self._set_col_series_on_df(col_name, df,
                                           col_series_as_strings)

        # special handling for period index columns: call to_timestamp to
        # convert the series to a datetime series before displaying
        if len(self._period_columns) > 0:
            for col_name in self._period_columns:
                sort_column_name = self._sort_helper_columns.get(col_name)
                if sort_column_name:
                    series_to_set = df[sort_column_name]
                else:
                    series_to_set = self._get_col_series_from_df(
                        col_name, df
                    ).to_timestamp()
                self._set_col_series_on_df(col_name, df, series_to_set)

        # and then call 'to_json' again to get a new version of the table
        # json that has interval columns replaced with text columns
        if len(self._interval_columns) > 0 or len(self._period_columns) > 0:
            df_json = pd_json.to_json(None, df,
                                      orient='table',
                                      date_format='iso',
                                      double_precision=self.precision)

        self._df_json = df_json
        if not update_columns:
            data_to_send = {
                'type': 'update_data_view',
                'columns': self._columns,
                'triggered_by': triggered_by
            }
            if scroll_to_row:
                data_to_send['scroll_to_row'] = scroll_to_row
            self.send(data_to_send)

    def _update_sort(self):
        try:
            if self._sort_field == '':
                return
            if self._sort_field in self._primary_key:
                if len(self._primary_key) == 1:
                    self._df.sort_index(
                        ascending=self._sort_ascending,
                        inplace=True
                    )
                else:
                    level_id = self._sort_field
                    if self._sort_field.startswith('level_'):
                        level_id = int(self._sort_field[6:])
                    self._df.sort_index(
                        level=level_id,
                        ascending=self._sort_ascending,
                        inplace=True
                    )
            else:
                self._df.sort_values(
                    self._sort_field,
                    ascending=self._sort_ascending,
                    inplace=True
                )
        except TypeError:
            self.log.info('TypeError occurred, assuming mixed data type '
                          'column')
            # if there's a TypeError, assume it means that we have a mixed
            # type column, and attempt to create a stringified version of
            # the column to use for sorting/filtering
            self._df.sort_values(
                self._initialize_sort_column(self._sort_field),
                ascending=self._sort_ascending,
                inplace=True
            )

    # Add a new column which is a stringified version of the column whose name
    # was passed in, which can be used for sorting and filtering (to avoid
    # error caused by the type of data in the column, like having multiple
    # data types in a single column).
    def _initialize_sort_column(self, col_name, to_timestamp=False):
        sort_column_name = self._sort_helper_columns.get(col_name)
        if sort_column_name:
            return sort_column_name

        sort_col_series = \
            self._get_col_series_from_df(col_name, self._df)
        sort_col_series_unfiltered = \
            self._get_col_series_from_df(col_name, self._unfiltered_df)
        sort_column_name = str(col_name) + self._sort_col_suffix

        if to_timestamp:
            self._df[sort_column_name] = sort_col_series.to_timestamp()
            self._unfiltered_df[sort_column_name] = \
                sort_col_series_unfiltered.to_timestamp()
        else:
            self._df[sort_column_name] = sort_col_series.map(str)
            self._unfiltered_df[sort_column_name] = \
                sort_col_series_unfiltered.map(str)

        self._sort_helper_columns[col_name] = sort_column_name
        return sort_column_name

    def _handle_get_column_min_max(self, content):
        col_name = content['field']
        col_info = self._columns[col_name]
        if 'filter_info' in col_info and 'selected' in col_info['filter_info']:
            df_for_unique = self._unfiltered_df
        else:
            df_for_unique = self._df

        # if there's a period index column, add a sort column which has the
        # same values, but converted to timestamps instead of period objects.
        # we'll use that sort column for all subsequent sorts/filters.
        if col_name in self._period_columns:
            self._initialize_sort_column(col_name,
                                         to_timestamp=True)

        col_series = self._get_col_series_from_df(col_name, df_for_unique)
        if 'is_index' in col_info:
            col_series = pd.Series(col_series)

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
                        try:
                            unique.sort()
                        except TypeError:
                            sort_col_name = \
                                self._initialize_sort_column(col_name)
                            col_series = df_for_unique[sort_col_name]
                            unique = col_series.unique()
                            unique.sort()
                    unique_list = unique.tolist()
                    self._sorted_column_cache[col_name] = unique_list

            if content['search_val'] is not None:
                unique_list = [
                    k for k in unique_list if
                    content['search_val'].lower() in str(k).lower()
                ]

            # if the filter that we're opening is already active (as indicated
            # by the presence of a 'selected' attribute on the column's
            # filter_info attribute), show the selected rows at the top and
            # specify that they should be checked
            if 'filter_info' in col_info and \
               'selected' in col_info['filter_info']:
                col_filter_info = col_info['filter_info']
                col_filter_table = self._filter_tables[col_name]

                def get_value_from_filter_table(k):
                    return col_filter_table[k]
                selected_indices = col_filter_info['selected'] or []
                if selected_indices == 'all':
                    excluded_indices = col_filter_info['excluded'] or []
                    excluded_values = list(map(get_value_from_filter_table,
                                               excluded_indices))
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
                    selected_vals = list(map(get_value_from_filter_table,
                                             selected_indices))
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
                message_type = 'update_data_view_filter'
            else:
                message_type = 'column_min_max_updated'
            try:
                self.send({
                    'type': message_type,
                    'field': col_name,
                    'col_info': col_info
                })
            except ValueError:
                # if there's a ValueError, assume it's because we're
                # attempting to serialize something that can't be converted
                # to json, so convert all the values to strings.
                col_info['values'] = map(str, col_info['values'])
                self.send({
                    'type': message_type,
                    'field': col_name,
                    'col_info': col_info
                })

    # get any column from a dataframe, including index columns
    def _get_col_series_from_df(self, col_name, df):
        sort_column_name = self._sort_helper_columns.get(col_name)
        if sort_column_name:
            return df[sort_column_name]

        if col_name in self._primary_key:
            if len(self._primary_key) > 1:
                key_index = self._primary_key.index(col_name)
                return df.index.get_level_values(level=key_index)
            else:
                return df.index
        else:
            return df[col_name]

    def _set_col_series_on_df(self, col_name, df, col_series):
        if col_name in self._primary_key:
            col_series.name = col_name
            if len(self._primary_key) > 1:
                key_index = self._primary_key.index(col_name)
                df.index.set_levels(col_series, level=key_index, inplace=True)
            else:
                df.set_index(col_series, inplace=True)
        else:
            df[col_name] = col_series

    def _append_condition_for_column(self, col_name, filter_info, conditions):
        col_series = self._get_col_series_from_df(col_name,
                                                  self._unfiltered_df)
        if filter_info['type'] == 'slider':
            if filter_info['min'] is not None:
                conditions.append(col_series >= filter_info['min'])
            if filter_info['max'] is not None:
                conditions.append(col_series <= filter_info['max'])
        elif filter_info['type'] == 'date':
            if filter_info['min'] is not None:
                conditions.append(
                    col_series >= pd.to_datetime(filter_info['min'], unit='ms')
                )
            if filter_info['max'] is not None:
                conditions.append(
                    col_series <= pd.to_datetime(filter_info['max'], unit='ms')
                )
        elif filter_info['type'] == 'boolean':
            if filter_info['selected'] is not None:
                conditions.append(
                    col_series == filter_info['selected']
                )
        elif filter_info['type'] == 'text':
            if col_name not in self._filter_tables:
                return
            col_filter_table = self._filter_tables[col_name]
            selected_indices = filter_info['selected']
            excluded_indices = filter_info['excluded']

            def get_value_from_filter_table(i):
                return col_filter_table[i]
            if selected_indices == "all":
                if excluded_indices is not None and len(excluded_indices) > 0:
                    excluded_values = list(
                        map(get_value_from_filter_table, excluded_indices)
                    )
                    conditions.append(~col_series.isin(excluded_values))
            elif selected_indices is not None and len(selected_indices) > 0:
                selected_values = list(
                    map(get_value_from_filter_table, selected_indices)
                )
                conditions.append(col_series.isin(selected_values))

    def _handle_filter_changed(self, content):
        col_name = content['field']
        columns = self._columns.copy()
        col_info = columns[col_name]
        col_info['filter_info'] = content['filter_info']
        columns[col_name] = col_info

        conditions = []
        for key, value in columns.items():
            if 'filter_info' in value:
                self._append_condition_for_column(
                    key, value['filter_info'], conditions
                )

        self._columns = columns

        self._ignore_df_changed = True
        if len(conditions) == 0:
            self._df = self._unfiltered_df.copy()
        else:
            combined_condition = conditions[0]
            for c in conditions[1:]:
                combined_condition = combined_condition & c

            self._df = self._unfiltered_df[combined_condition].copy()

        if len(self._df) < self._viewport_range[0]:
            viewport_size = self._viewport_range[1] - self._viewport_range[0]
            range_top = max(0, len(self._df) - viewport_size)
            self._viewport_range = (range_top, range_top + viewport_size)

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
            col_info = self._columns[content['column']]
            try:
                val_to_set = content['value']
                if col_info['type'] == 'datetime':
                    val_to_set = pd.to_datetime(val_to_set)

                self._df.set_value(self._df.index[content['row_index']],
                                   content['column'], val_to_set)
                query = self._unfiltered_df[self._index_col_name] == \
                    content['unfiltered_index']
                self._unfiltered_df.loc[query, content['column']] = val_to_set
            except (ValueError, TypeError):
                msg = "Error occurred while attempting to edit the " \
                      "DataFrame. Check the notebook server logs for more " \
                      "information."
                self.log.exception(msg)
                self.send({
                    'type': 'show_error',
                    'error_msg': msg,
                    'triggered_by': 'add_row'
                })
                return
        elif content['type'] == 'selection_change':
            self._selected_rows = content['rows']
        elif content['type'] == 'viewport_changed':
            self._viewport_range = (content['top'], content['bottom'])
            self._update_table(triggered_by='viewport_changed')
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
            self._update_table(triggered_by='sort_changed')
        elif content['type'] == 'get_column_min_max':
            self._handle_get_column_min_max(content)
        elif content['type'] == 'filter_changed':
            self._handle_filter_changed(content)

    def get_changed_df(self):
        """
        Get a copy of the DataFrame that was used to create the current
        instance of QgridWidget which reflects the current state of the UI.
        This includes any sorting or filtering changes, as well as edits
        that have been made by double clicking cells.

        :rtype: DataFrame
        """
        col_names_to_drop = list(self._sort_helper_columns.values())
        col_names_to_drop.append(self._index_col_name)
        return self._df.drop(col_names_to_drop, axis=1)

    def get_selected_df(self):
        """
        Get a DataFrame which reflects the current state of the UI and only
        includes the currently selected row(s). Internally it calls
        ``get_changed_df()`` and then filters down to the selected rows
        using ``iloc``.

        :rtype: DataFrame
        """
        changed_df = self.get_changed_df()
        return changed_df.iloc[self._selected_rows]

    def get_selected_rows(self):
        """
        Get the currently selected rows.

        :rtype: List of integers
        """
        return self._selected_rows

    def add_row(self):
        """
        Append a row at the end of the dataframe by duplicating the
        last row and incrementing it's index by 1. The feature is only
        available for DataFrames that have an integer index.
        """
        df = self._df

        if not df.index.is_integer():
            msg = "Cannot add a row to a table with a non-integer index"
            self.send({
                'type': 'show_error',
                'error_msg': msg,
                'triggered_by': 'add_row'
            })
            return

        last_index = max(df.index)
        last = df.loc[last_index].copy()
        last.name += 1
        last[self._index_col_name] = last.name
        df.loc[last.name] = last.values
        self._unfiltered_df.loc[last.name] = last.values
        self._update_table(triggered_by='add_row',
                           scroll_to_row=df.index.get_loc(last.name))

    def remove_row(self):
        """
        Remove the current row from the table.
        """
        if self._multi_index:
            msg = "Cannot remove a row from a table with a multi index"
            self.send({
                'type': 'show_error',
                'error_msg': msg,
                'triggered_by': 'remove_row'
            })
            return
        selected_names = \
            map(lambda x: self._df.iloc[x].name, self._selected_rows)
        self._df.drop(selected_names, inplace=True)
        self._unfiltered_df.drop(selected_names, inplace=True)
        self._selected_rows = []
        self._update_table(triggered_by='remove_row')


# Alias for legacy support, since we changed the capitalization
QGridWidget = QgridWidget
