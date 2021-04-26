# ipyslickgrid

This is a fork of [qgrid](https://github.com/quantopian/qgrid) and it has been created for the sole purpose of supporting Jupyterlab 3. However, over time, it may be used for more than that.

## Running from source & testing your changes

1. Clone the repository from GitHub and cd into the top-level directory:

```bash
git clone https://github.com/8080labs/ipyslickgrids.git
cd ipyslickgrids
```

2. Install the current project in editable mode:

```bash
pip install -e .
```

3. Install the node packages that ipyslickgrids depends on and build ipyslickgrids's javascript using webpack:

```bash
cd js && npm install .
```

4. Install and enable ipyslickgrids's javascript in your local jupyter notebook environment:

```bash
jupyter nbextension install --py --symlink --sys-prefix ipyslickgrids && jupyter nbextension enable --py --sys-prefix ipyslickgrids
```

5. If desired, install the labextension:

```bash
jupyter labextension link js/
```

6. Run the notebook as you normally would with the following command:

```bash
jupyter notebook
```

### Manually testing server-side changes
If the code you need to change is in ipyslickgrids's python code, then restart the kernel of the notebook you're in and rerun any ipyslickgrids cells to see your changes take effect.

### Manually testing client-side changes
If the code you need to change is in ipyslickgrids's javascript or css code, repeat step 3 to rebuild ipyslickgrids's npm package, then refresh the browser tab where you're viewing your notebook to see your changes take effect.

### Running automated tests
There is a small python test suite which can be run locally by running the command pytest in the root folder of the repository.