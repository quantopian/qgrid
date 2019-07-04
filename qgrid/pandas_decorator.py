from pandas import DataFrame
from .grid import show_grid

def _show_grid(df, **kwargs):
   return show_grid(df, **kwargs)
   
DataFrame.show_grid = _show_grid
