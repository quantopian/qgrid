from qgrid import QgridWidget
import numpy as np
import pandas as pd

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
    view._handle_qgrid_msg_helper({
        'column': "Date",
        'row_index': 3,
        'type': "cell_change",
        'unfiltered_index': 0,
        'value': "2013-01-16T00:00:00.000+00:00"
    })

def test_add_row():
    view = QgridWidget(df=create_df())
    view._handle_qgrid_msg_helper({
        'type': 'add_row'
    })

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
        'type': 'sort_changed',
        'sort_field': 3,
        'sort_ascending': True
    })

    view._handle_qgrid_msg_helper({
        'type': 'sort_changed',
        'sort_field': 'level_0',
        'sort_ascending': True
    })

def test_interval_index():
    df = create_interval_index_df()
    df.set_index('time_bin', inplace=True)
    view = QgridWidget(df=df)

def test_multi_interval_index():
    df = create_interval_index_df()
    df['A'] = np.array([3] * 1000,dtype='int32')
    df.set_index(['time', 'time_bin'], inplace=True)
    view = QgridWidget(df=df)


