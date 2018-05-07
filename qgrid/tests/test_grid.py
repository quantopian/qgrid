from qgrid import (
    QgridWidget,
    set_defaults,
    show_grid
)
import numpy as np
import pandas as pd
import json

def create_df():
    return pd.DataFrame({
        'A' : 1.,
        'Date' : pd.Timestamp('20130102'),
        'C' : pd.Series(1,index=list(range(4)),dtype='float32'),
        'D' : np.array([3] * 4,dtype='int32'),
        'E' : pd.Categorical(["test","train","foo","bar"]),
        'F' : ['foo', 'bar', 'buzz', 'fox']
    })

def create_multi_index_df():
    arrays = [['bar', 'bar', 'baz', 'baz', 'foo', 'foo', 'qux', 'qux'],
          ['one', 'two', 'one', 'two', 'one', 'two', 'one', 'two']]
    return pd.DataFrame(np.random.randn(8, 4), index=arrays)

def create_interval_index_df():
    td = np.cumsum(np.random.randint(1, 15*60, 1000))
    start = pd.Timestamp('2017-04-17')
    df = pd.DataFrame(
    [(start + pd.Timedelta(seconds=d)) for d in td],
    columns=['time'])

    freq = '15Min'
    start = df['time'].min().floor(freq)
    end = df['time'].max().ceil(freq)
    bins = pd.date_range(start, end, freq=freq)
    df['time_bin'] = pd.cut(df['time'], bins)
    return df

def test_edit_date():
    view = QgridWidget(df=create_df())
    check_edit_success(view,
                       'Date',
                       3,
                       "2013-01-02T00:00:00.000Z",
                       pd.Timestamp('2013-01-16 00:00:00'),
                       "2013-01-16T00:00:00.000Z")

def check_edit_success(widget,
                       col_name,
                       row_index,
                       old_value,
                       new_val_obj,
                       new_val_json):

    observer_called = {}
    def on_value_change(change):
        observer_called['called'] = True
        assert change['new'][col_name][row_index] == new_val_obj

    widget.observe(on_value_change, names=['_df'])

    grid_data = json.loads(widget._df_json)['data']
    assert grid_data[row_index][col_name] == old_value

    widget._handle_qgrid_msg_helper({
        'column': col_name,
        'row_index': row_index,
        'type': "cell_change",
        'unfiltered_index': row_index,
        'value': new_val_json
    })

    assert observer_called['called']
    widget.unobserve(on_value_change, names=['_df'])

    # call _update_table so the widget updates _df_json
    widget._update_table(fire_data_change_event=False)
    grid_data = json.loads(widget._df_json)['data']
    assert grid_data[row_index][col_name] == new_val_json

def test_edit_number():
    old_val = 3
    view = QgridWidget(df=create_df())

    for idx in range(-10, 10, 1):
        check_edit_success(view, 'D', 2, old_val, idx, idx)
        old_val = idx

def test_add_row():
    view = QgridWidget(df=create_df())

    observer_called = {}
    def on_value_change(change):
        observer_called['called'] = True
        assert len(change['new']) == 5

    view.observe(on_value_change, names=['_df'])

    view._handle_qgrid_msg_helper({
        'type': 'add_row'
    })

    assert observer_called['called']

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
    df = pd.DataFrame([(pd.Timestamp('2017-02-02'), np.nan), (4, 2), ('foo', 'bar')])
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
        'type': "selection_change"
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
    view = QgridWidget(df=create_multi_index_df())

    observer_called = {'count': 0}
    def on_value_change(_):
        observer_called['count'] += 1

    view.observe(on_value_change, names=['_df'])

    view._handle_qgrid_msg_helper({
        'type': 'get_column_min_max',
        'field': 'level_0',
        'search_val': None
    })

    view._handle_qgrid_msg_helper({
        'type': 'filter_changed',
        'field': 3,
        'filter_info': {
            'field': 3,
            'type': 'slider',
            'min': -0.111,
            'max': None
        }
    })

    view._handle_qgrid_msg_helper({
        'type': 'filter_changed',
        'field': 3,
        'filter_info': {
            'field': 3,
            'type': 'slider',
            'min': None,
            'max': None
        }
    })

    view._handle_qgrid_msg_helper({
        'type': 'sort_changed',
        'sort_field': 3,
        'sort_ascending': True
    })

    view._handle_qgrid_msg_helper({
        'type': 'sort_changed',
        'sort_field': 'level_0',
        'sort_ascending': True
    })

    assert observer_called['count'] == 4

def test_interval_index():
    df = create_interval_index_df()
    df.set_index('time_bin', inplace=True)
    view = QgridWidget(df=df)

def test_multi_interval_index():
    df = create_interval_index_df()
    df['A'] = np.array([3] * 1000,dtype='int32')
    df.set_index(['time', 'time_bin'], inplace=True)
    view = QgridWidget(df=df)

def test_set_defaults():
    fake_grid_options_a = {'foo':'bar'}
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


def test_add_row_internally():
    df = pd.DataFrame({'foo': ['hello'], 'bar': ['world'], 'baz': [42], 'boo': [57]})
    df.set_index('baz', inplace=True, drop=True)

    q = QgridWidget(df=df)

    new_row = [
        ('baz', 43),
        ('bar', "new bar"),
        ('boo', 58),
        ('foo', "new foo")
    ]

    q.add_row_internally(new_row)

    assert q._df.loc[43, 'foo'] == 'new foo'
    assert q._df.loc[42, 'foo'] == 'hello'


def test_set_value_internally():
    df = pd.DataFrame({'foo': ['hello'], 'bar': ['world'], 'baz': [42], 'boo': [57]})
    df.set_index('baz', inplace=True, drop=True)

    q = QgridWidget(df=df)

    q.set_value_internally(42, 'foo', 'hola')

    assert q._df.loc[42, 'foo'] == 'hola'
