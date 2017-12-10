.. image:: https://media.quantopian.com/logos/open_source/qgrid-logo-03.png
    :target: https://qgrid.readthedocs.io
    :width: 190px
    :align: center
    :alt: qgrid

=====
qgrid
=====
Qgrid is a Jupyter notebook widget which uses `SlickGrid <https://github.com/mleibman/SlickGrid>`_ to render pandas
DataFrames within a Jupyter notebook. This allows you to explore your DataFrames with intuitive scrolling, sorting, and
filtering controls, as well as edit your DataFrames by double clicking cells.

We originally developed qgrid for use in `Quantopian's hosted research environment
<https://www.quantopian.com/research?utm_source=github&utm_medium=web&utm_campaign=qgrid-repo>`_ in fall of 2014, but had to put it on the backburner for a while so we could focus on higher priority projects.

Qgrid development started up again in summer 2017, when we started a major refactoring project to allow qgrid to take advantage of the latest advances in ipywidgets (specifically, ipywidget 7.x).  As a part of this refactoring we also moved qgrid's sorting, and filtering logic from the client (javascript) to the server (python). This new version is called
qgrid 1.0, and the instructions that follow are for this new version.

Demo
----
Click the badge below to try out qgrid in a live sample notebook:

.. image:: https://beta.mybinder.org/badge.svg 
    :target: https://beta.mybinder.org/v2/gh/quantopian/qgrid-notebooks/master?filepath=index.ipynb

*You'll see a brief loading screen while a notebook server is being created for you in the
cloud.  This shouldn't take more than a minute, and usually completes in under 10 seconds.*

API Documentation
-----------------
API documentation is hosted on `readthedocs <http://qgrid.readthedocs.io/en/latest/>`_.

Installation
------------

Run the following to install and enable qgrid::

  pip install qgrid --pre
  jupyter nbextension enable --py --sys-prefix qgrid

  OR

  conda install -c tim_shawver/label/dev qgrid==1.0.0b9

If you haven't enabled the ipywidgets nbextension yet, you'll need to also run this command::

  jupyter nbextension enable --py --sys-prefix widgetsnbextension

At this point you should be able to run a notebook server and use qgrid.

Jupyterlab Installation
-----------------------

First, go through the normal installation steps above as you normally would when using qgrid in the notebook.
If you haven't already install jupyterlab and enabled ipywidgets, do that first with the following lines::

  pip install jupyterlab
  jupyter labextension install @jupyter-widgets/jupyterlab-manager
  jupyter labextension enable @jupyter-widgets/jupyterlab-manager

Install the qgrid-jupyterlab extension and enable::

  jupyter labextension install qgrid@1.0.0-beta.10

At this point if you run jupyter lab normally with the 'jupyter lab' command, you should be
able to use qgrid in notebooks as you normally would.

*Please Note: Jupyterlab support has been tested with jupyterlab 0.30.5 and jupyterlab-manager 0.31.3, so if you're
having trouble, try installing those versions. Feel free to file an issue if you find that qgrid isn't working
with a newer version of either dependency.*

Dependencies
------------

Qgrid runs on `Python 2 or 3 <https://www.python.org/downloads/>`_.  You'll also need
`pip <https://pypi.python.org/pypi/pip>`_ for the installation steps below.

Qgrid depends on the following three Python packages:

    `Jupyter notebook <https://github.com/jupyter/notebook>`_
      This is the interactive Python environment in which qgrid runs.

    `ipywidgets <https://github.com/ipython/ipywidgets>`_
      In order for Jupyter notebooks to be able to run widgets, you have to also install this ipywidgets package.
      It's maintained by the Jupyter organization, the same people who created Jupyter notebook.

    `Pandas <http://pandas.pydata.org/>`_
      A powerful data analysis / manipulation library for Python.  Qgrid requires that the data to be rendered as an
      interactive grid be provided in the form of a pandas DataFrame.

These are listed in `requirements.txt <https://github.com/quantopian/qgrid/blob/master/requirements.txt>`_
and will be automatically installed (if necessary) when qgrid is installed via pip.

Compatibility
-------------

=================  ===========================  ==============================  ==============================
 qgrid             IPython / Jupyter notebook   ipywidgets                      Jupyterlab
=================  ===========================  ==============================  ==============================
 0.2.0             2.x                          N/A                             N/A
 0.3.x             3.x                          N/A                             N/A
 0.3.x             4.0                          4.0.x                           N/A
 0.3.x             4.1                          4.1.x                           N/A
 0.3.2             4.2                          5.x                             N/A
 0.3.3             5.x                          6.x                             N/A
 1.0.0b10          5.x                          7.x                             0.30.x
=================  ===========================  ==============================  ==============================


Running the demo notebook locally
---------------------------------

There's a demo notebook in the `qgrid-notebooks <https://github.com/quantopian/qgrid-notebooks/>`_ repository
which will help you get familiar with the functionality that qgrid provides. Here are the steps to clone the
qgrid-notebooks repository and run the demo notebook:

#. Clone the repository from GitHub::

    git clone https://github.com/quantopian/qgrid-notebooks.git

#. Go to the top-level directory of the qgrid-notebooks repository and run the notebook::

    cd qgrid-notebooks
    pip install -r requirements_dev.txt
    jupyter notebook


Running from source
-------------------

If you'd like to contribute to qgrid, or just want to be able to modify the source code for your own purposes, you'll
want to clone this repository and run qgrid from your local copy of the repository.  The following steps explain how
to do this.

#. Clone the repository from GitHub and ``cd`` into the top-level directory::

    git clone https://github.com/quantopian/qgrid.git
    cd qgrid

#. Install the current project in `editable <https://pip.pypa.io/en/stable/reference/pip_install/#editable-installs>`_
   mode::

    pip install -e .

#. Install the node packages that qgrid depends on and build qgrid's javascript using webpack::

    cd js && npm install .

#. Install and enable qgrid's javascript in your local jupyter notebook environment::

    jupyter nbextension install --py --symlink --sys-prefix qgrid && jupyter nbextension enable --py --sys-prefix qgrid

#. Run the notebook as you normally would with the following command::

    jupyter notebook

#. If the code you need to change is in qgrid's python code, then restart the kernel of the notebook you're in and
   rerun any qgrid cells to see your changes take effect.

#. If the code you need to change is in qgrid's javascript code, repeat step 3 to rebuild qgrid's javascript, then
   refresh the browser tab where you're viewing your notebook to see your changes take effect.

Continuing to use qgrid 0.3.3
-----------------------------
If you're looking for the installation and usage instructions for qgrid 0.3.3 and the sample notebook that goes
along with it, please see the `qgrid 0.3.3 tag <https://github.com/quantopian/qgrid/tree/v0.3.3>`_ in this
repository. The installation steps will be mostly the same. The only difference is that when you run "pip install"
you'll have to explicitly specify that you want to install version 0.3.3, like this::

  pip install qgrid==0.3.3

If you're looking for the API docs, you can find them on the
`readthedocs page for qgrid 0.3.3 <http://qgrid.readthedocs.io/en/v0.3.3/>`_.

If you're looking for the demo notebook for 0.3.3, it's still availabe `in nbviewer
<http://nbviewer.jupyter.org/gist/TimShawver/8fcef51dd3c222ed25306c002ab89b60>`_.

Qgrid 0.3.3 is not compatible with ipywidgets 7, so if you need support for ipywidgets 7, you'll need to use
qgrid 1.0.
