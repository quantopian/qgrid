.. qgrid documentation master file, created by
   sphinx-quickstart on Tue Sep  1 11:25:28 2015.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

.. image:: https://media.quantopian.com/logos/open_source/qgrid-logo-03.png
    :target: https://qgrid.readthedocs.io
    :width: 190px
    :align: center
    :alt: qgrid

Qgrid API Documentation
=======================

Qgrid is an `Jupyter notebook widget <https://github.com/ipython/ipywidgets>`_ which uses
`SlickGrid <https://github.com/mleibman/SlickGrid>`_ to render `pandas <https://github.com/pydata/pandas>`_ DataFrames
as interactive grid controls.

Other qgrid resources
---------------------

This page hosts only the API docs for the project.  You might also be interested in these other qgrid-related
resources:

`qgrid on GitHub <https://github.com/quantopian/qgrid>`_
  This is where you'll find the source code and the rest of the documentation for the project, including the
  instructions for installing and running qgrid.

`qgrid demo on binder <https://beta.mybinder.org/v2/gh/quantopian/qgrid-notebooks/master?filepath=index.ipynb>`_
  Click the badge below or the link above to try out qgrid in your browser.  You'll see a brief loading screen and
  then a notebook will appear:

  .. image:: https://beta.mybinder.org/badge.svg
    :target: https://beta.mybinder.org/v2/gh/quantopian/qgrid-notebooks/master?filepath=index.ipynb


:mod:`qgrid` Module
-------------------

.. automodule:: qgrid
    :members:
    :exclude-members: QgridWidget

    .. autoclass:: QgridWidget(df=None, grid_options=None, precision=None, show_toolbar=None)
        :members:
