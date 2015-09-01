qgrid
==============

Qgrid is an IPython extension which uses SlickGrid to render pandas DataFrames within an IPython notebook. It's 
being developed for use in [Quantopian's hosted research environment](https://www.quantopian.com/research?utm_source=github&utm_medium=web&utm_campaign=qgrid-repo), 
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

#### Installation:
Installation instruction can be found in the same notebook as the demo, [qgrid_demo.ipynb](http://nbviewer.ipython.org/github/quantopian/qgrid/blob/master/qgrid_demo.ipynb).

#### API Documentation:
Read the full [API documentation ](http://qgrid.readthedocs.org/en/latest/) on readthedocs.

#### How it works:

##### Background on nbextensions:
IPython notebook has a standard way of implementing purely client-side extensions, 
which involves placing the extension in the nbextensions folder and configuring IPython notebook to load it.
These "nbextensions" are able to respond to Javascript events that they're given access to through IPython 
notebook's Javascript API, and the examples I've seen tend to run some javascript once when the notebook is 
initialized.  For example, I've seen nbextensions that add a button to the notebook toolbar or create a 
floating table of contents.

Initially I was expecting that qgrid would be an nbextension because it's basically just a Javascript grid.  That 
turned out to mostly incorrect, and qgrid ended up being implemented as a python package that contains an 
nbextension.
 
##### Why not a standard nbextension?
* Qgrid needs to run Javascript at the time of cell execution rather than notebook startup.  
  * In particular, when `show_grid` gets called from a cell in an IPython notebook, qgrid needs to be able to inject 
HTML and Javascript into the DOM.   
* Qgrids are generated through a python API (i.e. the `show_grid` function), so there has to be some 
python code in the extension, for the purpose of providing that API.

##### Why not a standard IPython extension?
* Qgrid includes a bunch of Javascript/CSS files and `%install_ext` was designed for the case of installing an extension that consists of a single python file.  
  * pip is more well suited for the task of distributing a package with dependencies.
* Qgrid's API is a python module, so it makes sense for it to be distributed with pip, like any other python module.

##### The solution: A python package that contains an nbextension.
* The qgrid python package can be installed using pip, and the qgrid module can be imported using `import qgrid`
* The qgrid module includes an `nbinstall` function for installing qgrid's Javascript/CSS dependencies.  When 
`nbinstall` is run, the qgrid module copies it's Javascript/CSS folder into the nbextensions folder, effectively deploying it as an 
nbextension.
* The qgrid module also contains `show_grid`, which is the function that actually generates a qgrid from a 
DataFrame.  The show_grid function generates the qgrid by returning a custom object with its `_ipython_display_` 
function overridden.  I learned about this strategy from the "Custom Display Logic" sample notebook 
provided with the IPython git repository, found [here on GitHub](https://github.com/ipython/ipython/blob/master/examples/IPython%20Kernel/Custom%20Display%20Logic.ipynb).
