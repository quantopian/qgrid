from qgrid import QgridWidget
import numpy as np
import pandas as pd

def create_df():
    return pd.DataFrame({
        'A' : 1.,
        'Date' : pd.Timestamp('20130102'),
        'C' : pd.Series(1,index=list(range(4)),dtype='float32'),
        'D' : np.array([3] * 4,dtype='int32'),
        'E' : pd.Categorical(["test","train","test","train"]),
        'F' : 'foo'
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


