from qgrid import (
    QgridWidget,
    set_defaults,
    show_grid,
    on as qgrid_on
)
from traitlets import All
import numpy as np
import pandas as pd
import json


def create_df():
    return pd.DataFrame({
        'A': 1.,
        'Date': pd.Timestamp('20130102'),
        'C': pd.Series(1, index=list(range(4)), dtype='float32'),
        'D': np.array([3] * 4, dtype='int32'),
        'E': pd.Categorical(["test", "train", "foo", "bar"]),
        'F': ['foo', 'bar', 'buzz', 'fox']
    })


def create_large_df():
    large_df = pd.DataFrame(np.random.randn(10000, 4), columns=list('ABCD'))
    large_df['B (as str)'] = large_df['B'].map(lambda x: str(x))
    return large_df


def create_multi_index_df():
    arrays = [['bar', 'bar', 'baz', 'baz', 'foo', 'foo', 'qux', 'qux'],
              ['one', 'two', 'one', 'two', 'one', 'two', 'one', 'two']]
    return pd.DataFrame(np.random.randn(8, 4), index=arrays)


def create_interval_index_df():
    td = np.cumsum(np.random.randint(1, 15*60, 1000))
    start = pd.Timestamp('2017-04-17')
    df = pd.DataFrame(
        [(start + pd.Timedelta(seconds=d)) for d in td],
        columns=['time']
    )

    freq = '15Min'
    start = df['time'].min().floor(freq)
    end = df['time'].max().ceil(freq)
    bins = pd.date_range(start, end, freq=freq)
    df['time_bin'] = pd.cut(df['time'], bins)
    return df


def init_event_history(event_names, widget=None):
    event_history = []

    def on_change(event, qgrid_widget):
        event_history.append(event)

    if widget is not None:
        widget.on(event_names, on_change)
    else:
        qgrid_on(event_names, on_change)

    return event_history


def test_edit_date():
    view = QgridWidget(df=create_df())
    check_edit_success(view,
                       'Date',
                       3,
                       pd.Timestamp('2013-01-02 00:00:00'),
                       "2013-01-02T00:00:00.000Z",
                       pd.Timestamp('2013-01-16 00:00:00'),
                       "2013-01-16T00:00:00.000Z")


def check_edit_success(widget,
                       col_name,
                       row_index,
                       old_val_obj,
                       old_val_json,
                       new_val_obj,
                       new_val_json):

    event_history = init_event_history('cell_edited', widget)

    grid_data = json.loads(widget._df_json)['data']
    assert grid_data[row_index][col_name] == old_val_json

    widget._handle_qgrid_msg_helper({
        'column': col_name,
        'row_index': row_index,
        'type': "cell_change",
        'unfiltered_index': row_index,
        'value': new_val_json
    })

    assert event_history == [{
        'name':  'cell_edited',
        'index':  row_index,
        'column': col_name,
        'old': old_val_obj,
        'new': new_val_obj
    }]
    assert widget._df[col_name][row_index] == new_val_obj

    # call _update_table so the widget updates _df_json
    widget._update_table(fire_data_change_event=False)
    grid_data = json.loads(widget._df_json)['data']
    assert grid_data[row_index][col_name] == new_val_json


def test_edit_number():
    old_val = 3
    view = QgridWidget(df=create_df())

    for idx in range(-10, 10, 1):
        check_edit_success(view, 'D', 2, old_val, old_val, idx, idx)
        old_val = idx


def test_add_row():
    widget = QgridWidget(df=create_df())
    event_history = init_event_history('row_added', widget=widget)

    widget._handle_qgrid_msg_helper({
        'type': 'add_row'
    })

    assert event_history == [{
        'name': 'row_added',
        'index': 4
    }]

    # make sure the added row in the internal dataframe contains the
    # expected values
    added_index = event_history[0]['index']
    expected_values = np.array(
        [4, 1.0, 1.0, 3, pd.Timestamp('2013-01-02 00:00:00'), 'bar', 'fox'],
        dtype=object
    )
    assert (widget._df.loc[added_index].values == expected_values).all()


def test_remove_row():
    widget = QgridWidget(df=create_df())
    event_history = init_event_history(['row_removed', 'selection_changed'],
                                       widget=widget)

    selected_rows = [1, 2]
    widget._handle_qgrid_msg_helper({
        'rows': selected_rows,
        'type': "selection_changed"
    })

    widget._handle_qgrid_msg_helper({
        'type': 'remove_row'
    })

    assert event_history == [
        {
            'name': 'selection_changed',
            'old': [],
            'new': selected_rows
        },
        {
            'name': 'row_removed',
            'indices': selected_rows
        }
    ]


def test_mixed_type_column():
    df = pd.DataFrame({'A': [1.2, 'xy', 4], 'B': [3, 4, 5]})
    df = df.set_index(pd.Index(['yz', 7, 3.2]))
    view = QgridWidget(df=df)
    view._handle_qgrid_msg_helper({
        'type': 'sort_changed',
        'sort_field': 'A',
        'sort_ascending': True
    })
    view._handle_qgrid_msg_helper({
        'type': 'get_column_min_max',
        'field': 'A',
        'search_val': None
    })


def test_nans():
    df = pd.DataFrame([(pd.Timestamp('2017-02-02'), np.nan),
                       (4, 2),
                       ('foo', 'bar')])
    view = QgridWidget(df=df)
    view._handle_qgrid_msg_helper({
        'type': 'sort_changed',
        'sort_field': 1,
        'sort_ascending': True
    })
    view._handle_qgrid_msg_helper({
        'type': 'get_column_min_max',
        'field': 1,
        'search_val': None
    })


def test_period_object_column():
    range_index = pd.period_range(start='2000', periods=10, freq='B')
    df = pd.DataFrame({'a': 5, 'b': range_index}, index=range_index)
    view = QgridWidget(df=df)
    view._handle_qgrid_msg_helper({
        'type': 'sort_changed',
        'sort_field': 'index',
        'sort_ascending': True
    })
    view._handle_qgrid_msg_helper({
        'type': 'get_column_min_max',
        'field': 'index',
        'search_val': None
    })
    view._handle_qgrid_msg_helper({
        'type': 'sort_changed',
        'sort_field': 'b',
        'sort_ascending': True
    })
    view._handle_qgrid_msg_helper({
        'type': 'get_column_min_max',
        'field': 'b',
        'search_val': None
    })


def test_get_selected_df():
    sample_df = create_df()
    selected_rows = [1, 3]
    view = QgridWidget(df=sample_df)
    view._handle_qgrid_msg_helper({
        'rows': selected_rows,
        'type': "selection_changed"
    })
    selected_df = view.get_selected_df()
    assert len(selected_df) == 2
    assert sample_df.iloc[selected_rows].equals(selected_df)


def test_integer_index_filter():
    view = QgridWidget(df=create_df())
    view._handle_qgrid_msg_helper({
        'field': "index",
        'filter_info': {
            'field': "index",
            'max': None,
            'min': 2,
            'type': "slider"
        },
        'type': "filter_changed"
    })
    filtered_df = view.get_changed_df()
    assert len(filtered_df) == 2


def test_series_of_text_filters():
    view = QgridWidget(df=create_df())
    view._handle_qgrid_msg_helper({
        'type': 'get_column_min_max',
        'field': 'E',
        'search_val': None
    })
    view._handle_qgrid_msg_helper({
        'field': "E",
        'filter_info': {
            'field': "E",
            'selected': [0, 1],
            'type': "text",
            'excluded': []
        },
        'type': "filter_changed"
    })
    filtered_df = view.get_changed_df()
    assert len(filtered_df) == 2

    # reset the filter...
    view._handle_qgrid_msg_helper({
        'field': "E",
        'filter_info': {
            'field': "E",
            'selected': None,
            'type': "text",
            'excluded': []
        },
        'type': "filter_changed"
    })

    # ...and apply a text filter on a different column
    view._handle_qgrid_msg_helper({
        'type': 'get_column_min_max',
        'field': 'F',
        'search_val': None
    })
    view._handle_qgrid_msg_helper({
        'field': "F",
        'filter_info': {
            'field': "F",
            'selected': [0, 1],
            'type': "text",
            'excluded': []
        },
        'type': "filter_changed"
    })
    filtered_df = view.get_changed_df()
    assert len(filtered_df) == 2


def test_date_index():
    df = create_df()
    df.set_index('Date', inplace=True)
    view = QgridWidget(df=df)
    view._handle_qgrid_msg_helper({
        'type': 'filter_changed',
        'field': 'A',
        'filter_info': {
            'field': 'A',
            'type': 'slider',
            'min': 2,
            'max': 3
        }
    })


def test_multi_index():
    widget = QgridWidget(df=create_multi_index_df())
    event_history = init_event_history(['filter_dropdown_shown',
                                        'filter_changed',
                                        'sort_changed'], widget=widget)

    widget._handle_qgrid_msg_helper({
        'type': 'get_column_min_max',
        'field': 'level_0',
        'search_val': None
    })

    widget._handle_qgrid_msg_helper({
        'type': 'get_column_min_max',
        'field': 3,
        'search_val': None
    })

    widget._handle_qgrid_msg_helper({
        'type': 'filter_changed',
        'field': 3,
        'filter_info': {
            'field': 3,
            'type': 'slider',
            'min': -0.111,
            'max': None
        }
    })

    widget._handle_qgrid_msg_helper({
        'type': 'filter_changed',
        'field': 3,
        'filter_info': {
            'field': 3,
            'type': 'slider',
            'min': None,
            'max': None
        }
    })

    widget._handle_qgrid_msg_helper({
        'type': 'sort_changed',
        'sort_field': 3,
        'sort_ascending': True
    })

    widget._handle_qgrid_msg_helper({
        'type': 'sort_changed',
        'sort_field': 'level_0',
        'sort_ascending': True
    })

    assert event_history == [
        {
            'name': 'filter_dropdown_shown',
            'column': 'level_0'
        },
        {
            'name': 'filter_dropdown_shown',
            'column': 3
        },
        {
            'name': 'filter_changed',
            'column': 3
        },
        {
            'name': 'filter_changed',
            'column': 3
        },
        {
            'name': 'sort_changed',
            'old': {
                'column': None,
                'ascending': True
            },
            'new': {
                'column': 3,
                'ascending': True
            }
        },
        {
            'name': 'sort_changed',
            'old':
                {
                    'column': 3,
                    'ascending': True
                },
            'new':
                {
                    'column': 'level_0',
                    'ascending': True
                }
        }
    ]


def test_interval_index():
    df = create_interval_index_df()
    df.set_index('time_bin', inplace=True)
    show_grid(df)


def test_multi_interval_index():
    df = create_interval_index_df()
    df['A'] = np.array([3] * 1000, dtype='int32')
    df.set_index(['time', 'time_bin'], inplace=True)
    show_grid(df)


def test_set_defaults():
    fake_grid_options_a = {'foo': 'bar'}
    set_defaults(show_toolbar=False, precision=4,
                 grid_options=fake_grid_options_a)

    def assert_widget_vals_a(widget):
        assert not widget.show_toolbar
        assert widget.precision == 4
        assert widget.grid_options == fake_grid_options_a

    df = create_df()
    view = show_grid(df)
    assert_widget_vals_a(view)

    view = QgridWidget(df=df)
    assert_widget_vals_a(view)

    fake_grid_options_b = {'foo': 'buzz'}
    set_defaults(show_toolbar=True, precision=2,
                 grid_options=fake_grid_options_b)

    def assert_widget_vals_b(widget):
        assert widget.show_toolbar
        assert widget.precision == 2
        assert widget.grid_options == fake_grid_options_b

    df = create_df()
    view = show_grid(df)
    assert_widget_vals_b(view)

    view = QgridWidget(df=df)
    assert_widget_vals_b(view)


class MyObject(object):
    def __init__(self, obj):
        self.obj = obj


my_object_vals = [MyObject(MyObject(None)), MyObject(None)]


def test_object_dtype():
    df = pd.DataFrame({'a': my_object_vals})
    widget = QgridWidget(df=df)
    grid_data = json.loads(widget._df_json)['data']

    widget._handle_qgrid_msg_helper({
        'type': 'get_column_min_max',
        'field': 'a',
        'search_val': None
    })
    widget._handle_qgrid_msg_helper({
        'field': "a",
        'filter_info': {
            'field': "a",
            'selected': [0, 1],
            'type': "text",
            'excluded': []
        },
        'type': "filter_changed"
    })

    filter_table = widget._filter_tables['a']
    assert not isinstance(filter_table[0], dict)
    assert not isinstance(filter_table[1], dict)

    assert not isinstance(grid_data[0]['a'], dict)
    assert not isinstance(grid_data[1]['a'], dict)


def test_object_dtype_categorical():
    cat_series = pd.Series(
        pd.Categorical(my_object_vals,
                       categories=my_object_vals)
    )
    widget = show_grid(cat_series)
    constraints_enum = widget._columns[0]['constraints']['enum']
    assert not isinstance(constraints_enum[0], dict)
    assert not isinstance(constraints_enum[1], dict)

    widget._handle_qgrid_msg_helper({
        'type': 'get_column_min_max',
        'field': 0,
        'search_val': None
    })
    widget._handle_qgrid_msg_helper({
        'field': 0,
        'filter_info': {
            'field': 0,
            'selected': [0],
            'type': "text",
            'excluded': []
        },
        'type': "filter_changed"
    })
    assert len(widget._df) == 1
    assert widget._df[0][0] == cat_series[0]


def test_viewport_changed():
    widget = QgridWidget(df=create_large_df())
    event_history = init_event_history(All)

    widget._handle_qgrid_msg_helper({
        'type': 'viewport_changed',
        'top': 7124,
        'bottom': 7136
    })

    assert event_history == [
        {
            'name': 'json_updated',
            'triggered_by': 'viewport_changed',
            'range': (7024, 7224)
        },
        {
            'name': 'viewport_changed',
            'old': (0, 100),
            'new': (7124, 7136)
        }
    ]


def test_viewport_changed_filter():
    widget = QgridWidget(df=create_large_df())
    event_history = init_event_history(All)

    widget._handle_qgrid_msg_helper({
        'type': 'get_column_min_max',
        'field': 'B (as str)',
        'search_val': None
    })

    widget._handle_qgrid_msg_helper({
        'type': 'viewport_changed_filter',
        'field': 'B (as str)',
        'top': 556,
        'bottom': 568
    })

    widget._handle_qgrid_msg_helper({
        'type': 'viewport_changed_filter',
        'field': 'B (as str)',
        'top': 302,
        'bottom': 314
    })

    assert event_history == [
        {
            'name': 'filter_dropdown_shown',
            'column': 'B (as str)'
        },
        {
            'name': 'text_filter_viewport_changed',
            'column': 'B (as str)',
            'old': (0, 200),
            'new': (556, 568)
        },
        {
            'name': 'text_filter_viewport_changed',
            'column': 'B (as str)',
            'old': (556, 568),
            'new': (302, 314)
        }
    ]


def test_selection_changed():
    widget = QgridWidget(df=create_df())
    event_history = init_event_history('selection_changed', widget=widget)

    widget._handle_qgrid_msg_helper({
        'type': 'selection_changed',
        'rows': [5]
    })

    widget._handle_qgrid_msg_helper({
        'type': 'selection_changed',
        'rows': [7, 8]
    })

    assert event_history == [
        {
            'name': 'selection_changed',
            'old': [],
            'new': [5]
        },
        {
            'name': 'selection_changed',
            'old': [5],
            'new': [7, 8]
        },
    ]


def test_instance_created():
    event_history = init_event_history(All)
    qgrid_widget = show_grid(create_df())

    assert event_history == [
        {
            'name': 'instance_created'
        }
    ]
    assert qgrid_widget.id
