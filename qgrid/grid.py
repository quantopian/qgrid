import ipywidgets as widgets
import pandas as pd
import numpy as np
import json

from types import FunctionType
from IPython.display import display
from numbers import Integral
from traitlets import (
    Unicode,
    Instance,
    Bool,
    Integer,
    Dict,
    List,
    Tuple,
    Any,
    All,
    parse_notifier_name
)
from itertools import chain
from uuid import uuid4
from six import string_types

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
            'minVisibleRows': 8,
            'sortable': True,
            'filterable': True,
            'highlightSelectedCell': False,
            'highlightSelectedRow': True,
            'boldIndex': True
        }
        self._column_options = {
            'editable': True,
            # the following options are supported by SlickGrid
            'defaultSortAsc': True,
            'maxWidth': None,
            'minWidth': 30,
            'resizable': True,
            'sortable': True,
            'toolTip': "",
            'width': None
        }
        self._show_toolbar = False
        self._precision = None  # Defer to pandas.get_option

    def set_grid_option(self, optname, optvalue):
        self._grid_options[optname] = optvalue

    def set_defaults(self, show_toolbar=None, precision=None,
                     grid_options=None, column_options=None):
        if show_toolbar is not None:
            self._show_toolbar = show_toolbar
        if precision is not None:
            self._precision = precision
        if grid_options is not None:
            self._grid_options = grid_options
        if column_options is not None:
            self._column_options = column_options

    @property
    def show_toolbar(self):
        return self._show_toolbar

    @property
    def grid_options(self):
        return self._grid_options

    @property
    def precision(self):
        return self._precision or pd.get_option('display.precision') - 1

    @property
    def column_options(self):
        return self._column_options


class _EventHandlers(object):

    def __init__(self):
        self._listeners = {}

    def on(self, names, handler):
        names = parse_notifier_name(names)
        for n in names:
            self._listeners.setdefault(n, []).append(handler)

    def off(self, names, handler):
        names = parse_notifier_name(names)
        for n in names:
            try:
                if handler is None:
                    del self._listeners[n]
                else:
                    self._listeners[n].remove(handler)
            except KeyError:
                pass

    def notify_listeners(self, event, qgrid_widget):
        event_listeners = self._listeners.get(event['name'], [])
        all_listeners = self._listeners.get(All, [])
        for c in chain(event_listeners, all_listeners):
            c(event, qgrid_widget)


defaults = _DefaultSettings()
handlers = _EventHandlers()


def set_defaults(show_toolbar=None,
                 precision=None,
                 grid_options=None,
                 column_options=None):
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
    defaults.set_defaults(show_toolbar=show_toolbar,
                          precision=precision,
                          grid_options=grid_options,
                          column_options=column_options)


def on(names, handler):
    """
    Setup a handler to be called when a user interacts with any qgrid instance.

    Parameters
    ----------
    names : list, str, All
        If names is All, the handler will apply to all events.  If a list
        of str, handler will apply to all events named in the list.  If a
        str, the handler will apply just the event with that name.
    handler : callable
        A callable that is called when the event occurs. Its
        signature should be ``handler(event, qgrid_widget)``, where
        ``event`` is a dictionary and ``qgrid_widget`` is the QgridWidget
        instance that fired the event. The ``event`` dictionary at least
        holds a ``name`` key which specifies the name of the event that
        occurred.

    Notes
    -----
    There is also an ``on`` method on each individual QgridWidget instance,
    which works exactly like this one except it only listens for events on an
    individual instance (whereas this module-level method listens for events
    on all instances).

    See that instance-level method (linked below) for a list of all events
    that can be listened to via this module-level ``on`` method.  Both
    methods support the same events with one exception: the
    ``instance_create`` event.  This event is only available at the
    module-level and not on individual QgridWidget instances.

    The reason it's not available on individual qgrid instances is because
    the only time it fires is when a new instance is created. This means
    it's already done firing by the time a user has a chance to hook up any
    event listeners.

    Here's the full list of events that can be listened for via this
    module-level ``on`` method::

        [
            'instance_created',
            'cell_edited',
            'selection_changed',
            'viewport_changed',
            'row_added',
            'row_removed',
            'filter_dropdown_shown',
            'filter_changed',
            'sort_changed',
            'text_filter_viewport_changed',
            'json_updated'
        ]

    See Also
    --------
    QgridWidget.on :
        Same as this ``on`` method except it listens for events on an
        individual QgridWidget instance rather than on all instances.  See
        this method for a list of all the types of events that can be
        listened for via either ``on`` method.
    off:
        Unhook a handler that was hooked up using this ``on`` method.

    """
    handlers.on(names, handler)


def off(names, handler):
    """
    Remove a qgrid event handler that was registered with the ``on`` method.

    Parameters
    ----------
    names : list, str, All (default: All)
        The names of the events for which the specified handler should be
        uninstalled. If names is All, the specified handler is uninstalled
        from the list of notifiers corresponding to all events.
    handler : callable
        A callable that was previously registered with the 'on' method.

    See Also
    --------
    on:
        The method for hooking up handlers that this ``off`` method can remove.
    """
    handlers.off(names, handler)


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


def show_grid(data_frame,
              show_toolbar=None,
              precision=None,
              grid_options=None,
              column_options=None,
              column_definitions=None,
              row_edit_callback=None):
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

    :rtype: QgridWidget

    Parameters
    ----------
    data_frame : DataFrame
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
    column_options : dict
        Column options that are to be applied to every column. See the
        Notes section below for more information on the available options,
        as well as the default options that this widget uses.
    column_definitions : dict
        Column options that are to be applied to individual
        columns. The keys of the dict should be the column names, and each
        value should be the column options for a particular column,
        represented as a dict. The available options for each column are the
        same options that are available to be set for all columns via the
        ``column_options`` parameter. See the Notes section below for more
        information on those options.
    row_edit_callback : callable
        A callable that is called to determine whether a particular row
        should be editable or not. Its signature should be
        ``callable(row)``, where ``row`` is a dictionary which contains a
        particular row's values, keyed by column name. The callback should
        return True if the provided row should be editable, and False
        otherwise.


    Notes
    -----
    The following dictionary is used for ``grid_options`` if none are
    provided explicitly::

        {
            # SlickGrid options
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

            # Qgrid options
            'maxVisibleRows': 15,
            'minVisibleRows': 8,
            'sortable': True,
            'filterable': True,
            'highlightSelectedCell': False,
            'highlightSelectedRow': True
        }

    The first group of options are SlickGrid "grid options" which are
    described in the `SlickGrid documentation
    <https://github.com/mleibman/SlickGrid/wiki/Grid-Options>`_.

    The second group of option are options that were added specifically
    for Qgrid and therefore are not documented in the SlickGrid documentation.
    The following bullet points describe these options.

    * **maxVisibleRows** The maximum number of rows that Qgrid will show.
    * **minVisibleRows** The minimum number of rows that Qgrid will show
    * **sortable** Whether the Qgrid instance will allow the user to sort
      columns by clicking the column headers. When this is set to ``False``,
      nothing will happen when users click the column headers.
    * **filterable** Whether the Qgrid instance will allow the user to filter
      the grid. When this is set to ``False`` the filter icons won't be shown
      for any columns.
    * **highlightSelectedCell** If you set this to True, the selected cell
      will be given a light blue border.
    * **highlightSelectedRow** If you set this to False, the light blue
      background that's shown by default for selected rows will be hidden.

    The following dictionary is used for ``column_options`` if none are
    provided explicitly::

        {
            # SlickGrid column options
            'defaultSortAsc': True,
            'maxWidth': None,
            'minWidth': 30,
            'resizable': True,
            'sortable': True,
            'toolTip': "",
            'width': None

            # Qgrid column options
            'editable': True,
        }

    The first group of options are SlickGrid "column options" which are
    described in the `SlickGrid documentation
    <https://github.com/mleibman/SlickGrid/wiki/Column-Options>`_.

    The ``editable`` option was added specifically for Qgrid and therefore is
    not documented in the SlickGrid documentation.  This option specifies
    whether a column should be editable or not.

    See Also
    --------
    set_defaults : Permanently set global defaults for the parameters
                   of ``show_grid``, with the exception of the ``data_frame``
                   and ``column_definitions`` parameters, since those
                   depend on the particular set of data being shown by an
                   instance, and therefore aren't parameters we would want
                   to set for all QgridWidet instances.
    set_grid_option : Permanently set global defaults for individual
                      grid options.  Does so by changing the defaults
                      that the ``show_grid`` method uses for the
                      ``grid_options`` parameter.
    QgridWidget : The widget class that is instantiated and returned by this
                  method.

    """

    if show_toolbar is None:
        show_toolbar = defaults.show_toolbar
    if precision is None:
        precision = defaults.precision
    if not isinstance(precision, Integral):
        raise TypeError("precision must be int, not %s" % type(precision))
    if column_options is None:
        column_options = defaults.column_options
    else:
        options = defaults.column_options.copy()
        options.update(column_options)
        column_options = options
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

    column_definitions = (column_definitions or {})

    # create a visualization for the dataframe
    return QgridWidget(df=data_frame, precision=precision,
                       grid_options=grid_options,
                       column_options=column_options,
                       column_definitions=column_definitions,
                       row_edit_callback=row_edit_callback,
                       show_toolbar=show_toolbar)


PAGE_SIZE = 100


def stringify(x):
    if isinstance(x, string_types):
        return x
    else:
        return str(x)


@widgets.register()
class QgridWidget(widgets.DOMWidget):
    """
    The widget class which is instantiated by the ``show_grid`` method. This
    class can be constructed directly but that's not recommended because
    then default options have to be specified explicitly (since default
    options are normally provided by the ``show_grid`` method).

    The constructor for this class takes all the same parameters as
    ``show_grid``, with one exception, which is that the required
    ``data_frame`` parameter is replaced by an optional keyword argument
    called ``df``.

    See Also
    --------
    show_grid : The method that should be used to construct QgridWidget
                instances, because it provides reasonable defaults for all
                of the qgrid options.

    Attributes
    ----------
    df : DataFrame
        Get/set the DataFrame that's being displayed by the current instance.
        This DataFrame will NOT reflect any sorting/filtering/editing
        changes that are made via the UI. To get a copy of the DataFrame that
        does reflect sorting/filtering/editing changes, use the
        ``get_changed_df()`` method.
    grid_options : dict
        Get/set the grid options being used by the current instance.
    precision : integer
        Get/set the precision options being used by the current instance.
    show_toolbar : bool
        Get/set the show_toolbar option being used by the current instance.
    column_options : bool
        Get/set the column options being used by the current instance.
    column_definitions : bool
        Get/set the column definitions (column-specific options)
        being used by the current instance.

    """

    _view_name = Unicode('QgridView').tag(sync=True)
    _model_name = Unicode('QgridModel').tag(sync=True)
    _view_module = Unicode('qgrid').tag(sync=True)
    _model_module = Unicode('qgrid').tag(sync=True)
    _view_module_version = Unicode('1.1.1').tag(sync=True)
    _model_module_version = Unicode('1.1.1').tag(sync=True)

    _df = Instance(pd.DataFrame)
    _df_json = Unicode('').tag(sync=True)
    _primary_key = List()
    _primary_key_display = Dict({})
    _row_styles = Dict({}).tag(sync=True)
    _disable_grouping = Bool(False)
    _columns = Dict({}).tag(sync=True)
    _editable_rows = Dict({}).tag(sync=True)
    _filter_tables = Dict({})
    _sorted_column_cache = Dict({})
    _interval_columns = List([]).tag(sync=True)
    _period_columns = List([])
    _string_columns = List([])
    _sort_helper_columns = Dict({})
    _initialized = Bool(False)
    _ignore_df_changed = Bool(False)
    _unfiltered_df = Instance(pd.DataFrame)
    _index_col_name = Unicode('qgrid_unfiltered_index').tag(sync=True)
    _sort_col_suffix = Unicode('_qgrid_sort_column')
    _multi_index = Bool(False).tag(sync=True)
    _edited = Bool(False)
    _selected_rows = List([])
    _viewport_range = Tuple(Integer(),
                            Integer(),
                            default_value=(0, 100)).tag(sync=True)
    _df_range = Tuple(Integer(), Integer(), default_value=(0, 100)).tag(sync=True)
    _row_count = Integer(0).tag(sync=True)
    _sort_field = Any(None).tag(sync=True)
    _sort_ascending = Bool(True).tag(sync=True)
    _handlers = Instance(_EventHandlers)

    df = Instance(pd.DataFrame)
    precision = Integer(6).tag(sync=True)
    grid_options = Dict(sync=True)
    column_options = Dict({})
    column_definitions = Dict({})
    row_edit_callback = Instance(FunctionType, sync=False, allow_none=True)
    show_toolbar = Bool(False).tag(sync=True)
    id = Unicode(sync=True)

    def __init__(self, *args, **kwargs):
        self.id = str(uuid4())
        self._initialized = False
        super(QgridWidget, self).__init__(*args, **kwargs)
        # register a callback for custom messages
        self.on_msg(self._handle_qgrid_msg)
        self._initialized = True
        self._handlers = _EventHandlers()

        handlers.notify_listeners({
            'name': 'instance_created'
        }, self)

        if self.df is not None:
            self._update_df()

    def _grid_options_default(self):
        return defaults.grid_options

    def _precision_default(self):
        return defaults.precision

    def _show_toolbar_default(self):
        return defaults.show_toolbar

    def on(self, names, handler):
        """
        Setup a handler to be called when a user interacts with the current
        instance.

        Parameters
        ----------
        names : list, str, All
            If names is All, the handler will apply to all events.  If a list
            of str, handler will apply to all events named in the list.  If a
            str, the handler will apply just the event with that name.
        handler : callable
            A callable that is called when the event occurs. Its
            signature should be ``handler(event, qgrid_widget)``, where
            ``event`` is a dictionary and ``qgrid_widget`` is the QgridWidget
            instance that fired the event. The ``event`` dictionary at least
            holds a ``name`` key which specifies the name of the event that
            occurred.

        Notes
        -----
        Here's the list of events that you can listen to on QgridWidget
        instances via the ``on`` method::

            [
                'cell_edited',
                'selection_changed',
                'viewport_changed',
                'row_added',
                'row_removed',
                'filter_dropdown_shown',
                'filter_changed',
                'sort_changed',
                'text_filter_viewport_changed',
                'json_updated'
            ]

        The following bullet points describe the events listed above in more
        detail.  Each event bullet point is followed by sub-bullets which
        describe the keys that will be included in the ``event`` dictionary
        for each event.

        * **cell_edited** The user changed the value of a cell in the grid.

            * **index** The index of the row that contains the edited cell.
            * **column** The name of the column that contains the edited cell.
            * **old** The previous value of the cell.
            * **new** The new value of the cell.

        * **filter_changed** The user changed the filter setting for a column.

            * **column** The name of the column for which the filter setting
              was changed.

        * **filter_dropdown_shown** The user showed the filter control for a
          column by clicking the filter icon in the column's header.

            * **column** The name of the column for which the filter control
              was shown.

        * **json_updated** A user action causes QgridWidget to send rows of
          data (in json format) down to the browser. This happens as a side
          effect of certain actions such as scrolling, sorting, and filtering.

            * **triggered_by** The name of the event that resulted in
              rows of data being sent down to the browser.  Possible values
              are ``change_viewport``, ``change_filter``, ``change_sort``,
              ``add_row``, ``remove_row``, and ``edit_cell``.
            * **range** A tuple specifying the range of rows that have been
              sent down to the browser.

        * **row_added** The user added a new row using the "Add Row" button
          in the grid toolbar.

            * **index** The index of the newly added row.
            * **source** The source of this event.  Possible values are
              ``api`` (an api method call) and ``gui`` (the grid interface).

        * **row_removed** The user added removed one or more rows using the
          "Remove Row" button in the grid toolbar.

            * **indices** The indices of the removed rows, specified as an
              array of integers.
            * **source** The source of this event.  Possible values are
              ``api`` (an api method call) and ``gui`` (the grid interface).

        * **selection_changed** The user changed which rows were highlighted
          in the grid.

            * **old** An array specifying the indices of the previously
              selected rows.
            * **new** The indices of the rows that are now selected, again
              specified as an array.
            * **source** The source of this event.  Possible values are
              ``api`` (an api method call) and ``gui`` (the grid interface).

        * **sort_changed** The user changed the sort setting for the grid.

            * **old** The previous sort setting for the grid, specified as a
              dict with the following keys:

                * **column** The name of the column that the grid was sorted by
                * **ascending** Boolean indicating ascending/descending order

            * **new** The new sort setting for the grid, specified as a dict
              with the following keys:

                * **column** The name of the column that the grid is currently
                  sorted by
                * **ascending** Boolean indicating ascending/descending order

        * **text_filter_viewport_changed** The user scrolled the new rows
          into view in the filter dropdown for a text field.

            * **column** The name of the column whose filter dropdown is
              visible
            * **old** A tuple specifying the previous range of visible rows
              in the filter dropdown.
            * **new** A tuple specifying the range of rows that are now
              visible in the filter dropdown.

        * **viewport_changed** The user scrolled the new rows into view in
          the grid.

            * **old** A tuple specifying the previous range of visible rows.
            * **new** A tuple specifying the range of rows that are now
              visible.

        The ``event`` dictionary for every type of event will contain a
        ``name`` key specifying the name of the event that occurred.  That
        key is excluded from the lists of keys above to avoid redundacy.

        See Also
        --------
        on :
            Same as the instance-level ``on`` method except it listens for
            events on all instances rather than on an individual QgridWidget
            instance.
        QgridWidget.off:
            Unhook a handler that was hooked up using the instance-level
            ``on`` method.

        """
        self._handlers.on(names, handler)

    def off(self, names, handler):
        """
        Remove a qgrid event handler that was registered with the current
        instance's ``on`` method.

        Parameters
        ----------
        names : list, str, All (default: All)
            The names of the events for which the specified handler should be
            uninstalled. If names is All, the specified handler is uninstalled
            from the list of notifiers corresponding to all events.
        handler : callable
            A callable that was previously registered with the current
            instance's ``on`` method.

        See Also
        --------
        QgridWidget.on:
            The method for hooking up instance-level handlers that this
            ``off`` method can remove.

        """
        self._handlers.off(names, handler)

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

        self._update_table(update_columns=True, fire_data_change_event=False)
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
        self.send({'type': 'change_show_toolbar'})

    def _update_table(self,
                      update_columns=False,
                      triggered_by=None,
                      scroll_to_row=None,
                      fire_data_change_event=True):
        df = self._df.copy()

        from_index = max(self._viewport_range[0] - PAGE_SIZE, 0)
        to_index = max(self._viewport_range[0] + PAGE_SIZE, 0)
        new_df_range = (from_index, to_index)

        if triggered_by is 'viewport_changed' and \
                self._df_range == new_df_range:
            return

        self._df_range = new_df_range

        df = df.iloc[from_index:to_index]

        self._row_count = len(self._df.index)

        if update_columns:
            self._string_columns = list(df.select_dtypes(
                include=[np.dtype('O'), 'category']
            ).columns.values)

            def should_be_stringified(col_series):
                return col_series.dtype == np.dtype('O') or \
                       hasattr(col_series, 'cat') or \
                       isinstance(col_series, pd.PeriodIndex)

            if type(df.index) == pd.core.index.MultiIndex:
                self._multi_index = True
                for idx, cur_level in enumerate(df.index.levels):
                    if cur_level.name:
                        col_name = cur_level.name
                        self._primary_key_display[col_name] = col_name
                    else:
                        col_name = 'level_%s' % idx
                        self._primary_key_display[col_name] = ""
                    self._primary_key.append(col_name)
                    if should_be_stringified(cur_level):
                        self._string_columns.append(col_name)
            else:
                self._multi_index = False
                if df.index.name:
                    col_name = df.index.name
                    self._primary_key_display[col_name] = col_name
                else:
                    col_name = 'index'
                    self._primary_key_display[col_name] = ""
                self._primary_key = [col_name]

                if should_be_stringified(df.index):
                    self._string_columns.append(col_name)

        # call map(str) for all columns identified as string columns, in
        # case any are not strings already
        for col_name in self._string_columns:
            sort_column_name = self._sort_helper_columns.get(col_name)
            if sort_column_name:
                series_to_set = df[sort_column_name]
            else:
                series_to_set = self._get_col_series_from_df(
                    col_name, df, level_vals=True
                ).map(stringify)
            self._set_col_series_on_df(col_name, df, series_to_set)

        if type(df.index) == pd.core.index.MultiIndex and \
                not self._disable_grouping:
            previous_value = None
            row_styles = {}
            row_loc = from_index
            for index, row in df.iterrows():
                row_style = {}
                last_row = row_loc == (len(self._df) - 1)
                prev_idx = row_loc - 1
                for idx, index_val in enumerate(index):
                    col_name = self._primary_key[idx]
                    if previous_value is None:
                        row_style[col_name] = 'group-top'
                        continue
                    elif index_val == previous_value[idx]:
                        if prev_idx < 0:
                            row_style[col_name] = 'group-top'
                            continue
                        if row_styles[prev_idx][col_name] == 'group-top':
                            row_style[col_name] = 'group-middle'
                        elif row_styles[prev_idx][col_name] == 'group-bottom':
                            row_style[col_name] = 'group-top'
                        else:
                            row_style[col_name] = 'group-middle'
                    else:
                        if last_row:
                            row_style[col_name] = 'single'
                        else:
                            row_style[col_name] = 'group-top'
                        if prev_idx >= 0:
                            if row_styles[prev_idx][col_name] == \
                                    'group-middle':
                                row_styles[prev_idx][col_name] = 'group-bottom'
                            elif row_styles[prev_idx][col_name] == \
                                    'group-top':
                                row_styles[prev_idx][col_name] = 'group-single'
                previous_value = index
                row_styles[row_loc] = row_style
                row_loc += 1

            self._row_styles = row_styles
        else:
            self._row_styles = {}

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
                    cur_column['index_display_text'] = \
                        self._primary_key_display[col_name]
                    if len(self._primary_key) > 0:
                        cur_column['level'] = self._primary_key.index(col_name)
                    level = self._primary_key.index(col_name)
                    if level == 0:
                        cur_column['first_index'] = True
                    if self._multi_index and \
                       level == (len(self._primary_key) - 1):
                        cur_column['last_index'] = True

                cur_column['position'] = i
                cur_column['field'] = col_name
                cur_column['id'] = col_name
                cur_column['cssClass'] = cur_column['type']

                columns[col_name] = cur_column

                columns[col_name].update(self.column_options)
                if col_name in self.column_definitions.keys():
                    columns[col_name].update(self.column_definitions[col_name])

            self._columns = columns

        # special handling for interval columns: convert to a string column
        # and then call 'to_json' again to get a new version of the table
        # json that has interval columns replaced with text columns
        if len(self._interval_columns) > 0:
            for col_name in self._interval_columns:
                col_series = self._get_col_series_from_df(col_name,
                                                          df,
                                                          level_vals=True)
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
                        col_name, df, level_vals=True
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

        if self.row_edit_callback is not None:
            editable_rows = {}
            for index, row in df.iterrows():
                editable_rows[int(row[self._index_col_name])] = \
                    self.row_edit_callback(row)
            self._editable_rows = editable_rows

        if fire_data_change_event:
            self._notify_listeners({
                'name': 'json_updated',
                'triggered_by': triggered_by,
                'range': self._df_range
            })
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
            if self._sort_field is None:
                return
            self._disable_grouping = False
            if self._sort_field in self._primary_key:
                if len(self._primary_key) == 1:
                    self._df.sort_index(
                        ascending=self._sort_ascending,
                        inplace=True
                    )
                else:
                    level_index = self._primary_key.index(self._sort_field)
                    self._df.sort_index(
                        level=level_index,
                        ascending=self._sort_ascending,
                        inplace=True
                    )
                    if level_index > 0:
                        self._disable_grouping = True
            else:
                self._df.sort_values(
                    self._sort_field,
                    ascending=self._sort_ascending,
                    inplace=True
                )
                self._disable_grouping = True
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

    def _handle_show_filter_dropdown(self, content):
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
                unique_list = col_series.cat.categories
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
                max_items = PAGE_SIZE * 2
                range_max = length
                if length > max_items:
                    col_info['values'] = col_info['values'][:max_items]
                    range_max = max_items
                col_info['value_range'] = (0, range_max)

            col_info['viewport_range'] = col_info['value_range']
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
    def _get_col_series_from_df(self, col_name, df, level_vals=False):
        sort_column_name = self._sort_helper_columns.get(col_name)
        if sort_column_name:
            return df[sort_column_name]

        if col_name in self._primary_key:
            if len(self._primary_key) > 1:
                key_index = self._primary_key.index(col_name)
                if level_vals:
                    return df.index.levels[key_index]

                return df.index.get_level_values(key_index)
            else:
                return df.index
        else:
            return df[col_name]

    def _set_col_series_on_df(self, col_name, df, col_series):
        if col_name in self._primary_key:
            if len(self._primary_key) > 1:
                key_index = self._primary_key.index(col_name)
                prev_name = df.index.levels[key_index].name
                df.index.set_levels(col_series, level=key_index, inplace=True)
                df.index.rename(prev_name, level=key_index, inplace=True)
            else:
                prev_name = df.index.name
                df.set_index(col_series, inplace=True)
                df.index.rename(prev_name)
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

    def _handle_change_filter(self, content):
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
        self._update_table(triggered_by='change_filter')
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

        if content['type'] == 'edit_cell':
            col_info = self._columns[content['column']]
            try:
                location = (self._df.index[content['row_index']],
                            content['column'])

                val_to_set = content['value']
                if col_info['type'] == 'datetime':
                    val_to_set = pd.to_datetime(val_to_set)

                old_value = self._df.loc[location]
                self._df.loc[location] = val_to_set

                query = self._unfiltered_df[self._index_col_name] == \
                    content['unfiltered_index']
                self._unfiltered_df.loc[query, content['column']] = val_to_set
                self._notify_listeners({
                    'name': 'cell_edited',
                    'index': location[0],
                    'column': location[1],
                    'old': old_value,
                    'new': val_to_set,
                    'source': 'gui'
                })

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
        elif content['type'] == 'change_selection':
            self._change_selection(content['rows'], 'gui')
        elif content['type'] == 'change_viewport':
            old_viewport_range = self._viewport_range
            self._viewport_range = (content['top'], content['bottom'])

            # if the viewport didn't change, do nothing
            if old_viewport_range == self._viewport_range:
                return

            self._update_table(triggered_by='change_viewport')
            self._notify_listeners({
                'name': 'viewport_changed',
                'old': old_viewport_range,
                'new': self._viewport_range
            })

        elif content['type'] == 'add_row':
            row_index = self._duplicate_last_row()
            self._notify_listeners({
                'name': 'row_added',
                'index': row_index,
                'source': 'gui'
            })
        elif content['type'] == 'remove_row':
            removed_indices = self._remove_rows()
            self._notify_listeners({
                'name': 'row_removed',
                'indices': removed_indices,
                'source': 'gui'
            })
        elif content['type'] == 'change_filter_viewport':
            col_name = content['field']
            col_info = self._columns[col_name]
            col_filter_table = self._filter_tables[col_name]

            from_index = max(content['top'] - PAGE_SIZE, 0)
            to_index = max(content['top'] + PAGE_SIZE, 0)

            old_viewport_range = col_info['viewport_range']
            col_info['values'] = col_filter_table[from_index:to_index]
            col_info['value_range'] = (from_index, to_index)
            col_info['viewport_range'] = (content['top'], content['bottom'])

            self._columns[col_name] = col_info
            self.send({
                'type': 'update_data_view_filter',
                'field': col_name,
                'col_info': col_info
            })
            self._notify_listeners({
                'name': 'text_filter_viewport_changed',
                'column': col_name,
                'old': old_viewport_range,
                'new': col_info['viewport_range']
            })
        elif content['type'] == 'change_sort':
            old_column = self._sort_field
            old_ascending = self._sort_ascending
            self._sort_field = content['sort_field']
            self._sort_ascending = content['sort_ascending']
            self._sorted_column_cache = {}
            self._update_sort()
            self._update_table(triggered_by='change_sort')
            self._notify_listeners({
                'name': 'sort_changed',
                'old': {
                    'column': old_column,
                    'ascending': old_ascending
                },
                'new': {
                    'column': self._sort_field,
                    'ascending': self._sort_ascending
                }
            })
        elif content['type'] == 'show_filter_dropdown':
            self._handle_show_filter_dropdown(content)
            self._notify_listeners({
                'name': 'filter_dropdown_shown',
                'column': content['field']
            })
        elif content['type'] == 'change_filter':
            self._handle_change_filter(content)
            self._notify_listeners({
                'name': 'filter_changed',
                'column': content['field']
            })

    def _notify_listeners(self, event):
        # notify listeners at the module level
        handlers.notify_listeners(event, self)

        # notify listeners on this class instance
        self._handlers.notify_listeners(event, self)

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

    def add_row(self, row=None):
        """
        Append a row at the end of the DataFrame.  Values for the new row
        can be provided via the ``row`` argument, which is optional for
        DataFrames that have an integer index, and required otherwise.
        If the ``row`` argument is not provided, the last row will be
        duplicated and the index of the new row will be the index of
        the last row plus one.

        Parameters
        ----------
        row : list (default: None)
            A list of 2-tuples of (column name, column value) that specifies
            the values for the new row.

        See Also
        --------
        QgridWidget.remove_rows:
            The method for removing a row (or rows).
        """
        if row is None:
            added_index = self._duplicate_last_row()
        else:
            added_index = self._add_row(row)

        self._notify_listeners({
            'name': 'row_added',
            'index': added_index,
            'source': 'api'
        })

    def _duplicate_last_row(self):
        """
        Append a row at the end of the DataFrame by duplicating the
        last row and incrementing it's index by 1. The method is only
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
        return last.name

    def _add_row(self, row):
        """
        Append a new row to the end of the DataFrame given a list of 2-tuples
        of (column name, column value). This method will work for DataFrames
        with arbitrary index types.
        """
        df = self._df

        col_names, col_data = zip(*row)
        col_names = list(col_names)
        col_data = list(col_data)
        index_col_val = dict(row)[df.index.name]

        # check that the given column names match what
        # already exists in the dataframe
        required_cols = set(df.columns.values).union({df.index.name}) - \
            {self._index_col_name}
        if set(col_names) != required_cols:
            msg = "Cannot add row -- column names don't match in "\
                  "the existing dataframe"
            self.send({
                'type': 'show_error',
                'error_msg': msg,
                'triggered_by': 'add_row'
            })
            return

        for i, s in enumerate(col_data):
            if col_names[i] == df.index.name:
                continue

            df.loc[index_col_val, col_names[i]] = s
            self._unfiltered_df.loc[index_col_val, col_names[i]] = s

        self._update_table(triggered_by='add_row',
                           scroll_to_row=df.index.get_loc(index_col_val),
                           fire_data_change_event=True)

        return index_col_val

    def edit_cell(self, index, column, value):
        """
        Edit a cell of the grid, given the index and column of the cell
        to edit, as well as the new value of the cell. Results in a
        ``cell_edited`` event being fired.

        Parameters
        ----------
        index : object
            The index of the row containing the cell that is to be edited.
        column : str
            The name of the column containing the cell that is to be edited.
        value : object
            The new value for the cell.
        """
        old_value = self._df.loc[index, column]
        self._df.loc[index, column] = value
        self._unfiltered_df.loc[index, column] = value
        self._update_table(triggered_by='edit_cell',
                           fire_data_change_event=True)

        self._notify_listeners({
            'name': 'cell_edited',
            'index': index,
            'column': column,
            'old': old_value,
            'new': value,
            'source': 'api'
        })

    def remove_rows(self, rows=None):
        """
        Remove a row (or rows) from the DataFrame.  The indices of the
        rows to remove can be provided via the optional ``rows`` argument.
        If the ``rows`` argument is not provided, the row (or rows) that are
        currently selected in the UI will be removed.

        Parameters
        ----------
        rows : list (default: None)
            A list of indices of the rows to remove from the DataFrame. For
            a multi-indexed DataFrame, each index in the list should be a
            tuple, with each value in each tuple corresponding to a level of
            the MultiIndex.

        See Also
        --------
        QgridWidget.add_row:
            The method for adding a row.
        QgridWidget.remove_row:
            Alias for this method.
        """
        row_indices = self._remove_rows(rows=rows)
        self._notify_listeners({
            'name': 'row_removed',
            'indices': row_indices,
            'source': 'api'
        })
        return row_indices

    def remove_row(self, rows=None):
        """
        Alias for ``remove_rows``, which is provided for convenience
        because this was the previous name of that method.
        """
        return self.remove_rows(rows)

    def _remove_rows(self, rows=None):
        if rows is not None:
            selected_names = rows
        else:
            selected_names = \
                list(map(lambda x: self._df.iloc[x].name, self._selected_rows))

        self._df.drop(selected_names, inplace=True)
        self._unfiltered_df.drop(selected_names, inplace=True)
        self._selected_rows = []
        self._update_table(triggered_by='remove_row')
        return selected_names

    def change_selection(self, rows=[]):
        """
        Select a row (or rows) in the UI.  The indices of the
        rows to select are provided via the optional ``rows`` argument.

        Parameters
        ----------
        rows : list (default: [])
            A list of indices of the rows to select. For a multi-indexed
            DataFrame, each index in the list should be a tuple, with each
            value in each tuple corresponding to a level of the MultiIndex.
            The default value of ``[]`` results in the no rows being
            selected (i.e. it clears the selection).
        """
        new_selection = \
            list(map(lambda x: self._df.index.get_loc(x), rows))

        self._change_selection(new_selection, 'api', send_msg_to_js=True)

    def _change_selection(self, rows, source, send_msg_to_js=False):
        old_selection = self._selected_rows
        self._selected_rows = rows

        # if the selection didn't change, just return without firing
        # the event
        if old_selection == self._selected_rows:
            return

        if send_msg_to_js:
            data_to_send = {
                'type': 'change_selection',
                'rows': rows
            }
            self.send(data_to_send)

        self._notify_listeners({
            'name': 'selection_changed',
            'old': old_selection,
            'new': self._selected_rows,
            'source': source
        })

    def toggle_editable(self):
        """
        Change whether the grid is editable or not, without rebuilding
        the entire grid widget.
        """
        self.change_grid_option('editable', not self.grid_options['editable'])

    def change_grid_option(self, option_name, option_value):
        """
        Change a SlickGrid grid option without rebuilding the entire grid
        widget. Not all options are supported at this point so this
        method should be considered experimental.

        Parameters
        ----------
        option_name : str
            The name of the grid option to be changed.
        option_value : str
            The new value for the grid option.
        """
        self.grid_options[option_name] = option_value
        self.send({
            'type': 'change_grid_option',
            'option_name': option_name,
            'option_value': option_value
        })


# Alias for legacy support, since we changed the capitalization
QGridWidget = QgridWidget
