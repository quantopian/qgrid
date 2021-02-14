import {
  JupyterFrontEnd,
  JupyterFrontEndPlugin
} from '@jupyterlab/application';

/**
 * Initialization data for the qgrid2 extension.
 */
const extension: JupyterFrontEndPlugin<void> = {
  id: 'qgrid2:plugin',
  autoStart: true,
  activate: (app: JupyterFrontEnd) => {
    console.log('JupyterLab extension qgrid2 is activated!');
  }
};

export default extension;
