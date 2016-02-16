=====
qgrid
=====
Qgrid is an IPython widget which uses `SlickGrid <https://github.com/mleibman/SlickGrid>`_ to render pandas DataFrames
within a Jupyter notebook. This allows you to explore your DataFrames with intuitive scrolling, sorting, and
filtering controls, **as well as edit your DataFrames by double clicking a cell (new in v0.3.0)**.

We originally developed qgrid it for use in `Quantopian's hosted research environment
<https://www.quantopian.com/research?utm_source=github&utm_medium=web&utm_campaign=qgrid-repo>`_, but no longer have
a specific project in mind for using qgrid in the research environment.  For that reason we haven't been investing
much time in developing new features, and almost all of the forward development has come from the community. We've
mainly just been reviewing PR's, writing docs, and occasionally making small contributions.

Demo
----
See the demo by viewing `qgrid_demo.ipynb
<http://nbviewer.jupyter.org/gist/TimShawver/b4bc80d1128407c56c9a>`_ in nbviewer.

API Documentation
-----------------
API documentation is hosted on `readthedocs <http://qgrid.readthedocs.org/en/latest/>`_.

Installation
------------

**Python Dependencies:**

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

**Installing from PyPI:**

Qgrid is on `PyPI <https://pypi.python.org/pypi>`_ and can be installed like this::

    pip install qgrid

If you need to install a specific version of qgrid, pip allows you to specify it like this::

    pip install qgrid==0.2.0

See the `Releases <https://github.com/quantopian/qgrid/releases>`_ page for more details about the versions that
are available.

**Installing from GitHub:**

The latest release on PyPI is often out of date, and might not contain the latest bug fixes and features that you
want.  To run the latest code that is on master, install qgrid from GitHub instead of PyPI::

    pip install git+https://github.com/quantopian/qgrid

Running the demo locally
--------------------------

#. Go to the top-level directory of the qgrid repository and run the notebook::

    cd ~/qgrid
    jupyter notebook

   The advantage of running the notebook from the top-level directoy of the qgrid repository is the sample notebook
   that comes with qgrid will be available on the first page that appears when the web browser launches.  Here's what
   you can expect that page to look like:

     .. figure:: docs/images/home_screen.png
         :align: left
         :target: docs/images/home_screen.png
         :width: 800px

         The "notebook dashboard" for the jupyter notebook which shows all the files in the current directory.  Notice
         the demo notebook which is qgrid_demo.ipynb.

#. Click on qgrid_demo.ipynb to open it.  Here's what that will should like:

     .. figure:: docs/images/notebook_screen.png
         :align: left
         :target: docs/images/notebook_screen.png
         :width: 800px

         The demo notebook, qgrid_demo.ipynb, rendered by a locally-running Jupyter notebook.

#. Skip to the Notebook Installation section of the notebook because the Overview is copied from this document.
   Read the text and execute the cells as you come to them to complete the demo.

Running from source
-------------------

If you'd like to contribute to qgrid, or just want to be able to modify the source code for your own purposes, you'll
want to clone this repository and run qgrid from your local copy of the repository.  The following steps explain how
to do this.

#. Clone the repository from GitHub and ``cd`` into it the top-level directory::

    git clone https://github.com/quantopian/qgrid.git
    cd qgrid

#. Install the current project in `editable <https://pip.pypa.io/en/stable/reference/pip_install/#editable-installs>`_
   mode::

    pip install -e .

   This will install the packages that qgrid depends on in the normal way, but will do something special for the
   qgrid package itself.  Instead of copying the qgrid directory to the site-packages directory of the environment where
   it was installed (like a virualenv), pip will create a symbolic link which links to the directory you passed in to
   the ``pip install -e``.  The result is changes that you make to the source code will be reflected as soon as you restart
   the notebook.

   If you have virtualenv and virtualenvwrapper installed, an easy way to verify that this "editable" install succeeded
   is to do the following::

    cdsitepackages # navigate to the directory where virtualenv installs packages
    cat qgrid.egg-link # print out the contents of this symbolic link

   You should find that the symbolic link points to the top level directory of the qgrid repository which you ran
   the ``pip install -e`` command on.

#. Follow the instructions in the previous section to run qgrid.  Now when you make changes to qgrid's Python code,
   those changes will take effect as soon as you restart the Jupyter notebook server.

#. If the code you need to change is in qgrid's javascript, then call the
   `nb_install <http://qgrid.readthedocs.org/en/latest/#qgrid.nbinstall>`_ function from within the notebook to copy
   your latest changes to the "nbextensions" folder (i.e. where widgets must put their javascript for it to be found
   by the notebook).

Setting up your virtualenv
--------------------------

Using virtualenv is the recommended way of keeping Python dependencies for various project isolated.  The following
step help you set up a virtualenv for qgrid (which I'm sure most of you know how to do already).

Before you proceed with this section you'll need
`virtualenv and virtualenvwrapper <https://virtualenv.readthedocs.org/en/latest/>`_.  Install them like this::

    pip install virtualenv
    pip install virtualenvwrapper

#. Create a virtualenv for Jupyter notebook and qgrid::

    mkvirtualenv qgrid # create virtualenv called qgrid, and use Python 2 inside that virtualenv

   This will work but on my machine the resulting virtualenv will use whatever version of python comes up when you run
   ``python --version``, which in my case is Python 2.  If you want to use Python 3, specify the path to the version of
   Python you want to use, which for me looks like this::

    mkvirtualenv --python=/usr/local/bin/python3 qgrid # create virtualenv called qgrid, and use Python 3 inside that virtualenv

   You may have to change the ``/usr/local/bin/python3`` path depending on how you installed Python 3.  If you're unsure,
   type ``which python3`` to get the path to your Python 3 installation.

#. Install qgrid::

    pip install qgrid # see the "Installation" section above for more options
