qgrid
==============

Qgrid is an IPython extension which uses SlickGrid to render pandas DataFrames within an IPython notebook. It's 
being developed for use in [Quantopian's hosted research environment](https://www.quantopian.com/research), 
and this repository holds the latest source code.

#### Overview:
* [SlickGrid](https://github.com/mleibman/SlickGrid) is an an advanced javascript grid which allows users to scroll, 
sort, and filter hundreds of thousands of rows with extreme responsiveness.  
* [Pandas](https://github.com/pydata/pandas) is a powerful data analysis / manipulation library for Python, and
DataFrames are the primary way of storing and manipulating two-dimensional data in pandas.

Qgrid renders pandas DataFrames as SlickGrids, which enables users to explore 
the entire contents of a DataFrame using intuitive sorting and filtering controls.  It's designed to be used within 
IPython notebook, but it's also fully functional when rendered in [nbviewer](http://nbviewer.ipython.org/github/quantopian/qgrid/blob/master/qgrid_demo.ipynb).

#### Demo:
See the demo by viewing [qgrid_demo.ipynb](http://nbviewer.ipython.org/github/quantopian/qgrid/blob/master/qgrid_demo.ipynb) in nbviewer.
