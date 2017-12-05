import {
  IJupyterWidgetRegistry
 } from '@jupyter-widgets/base';


import {
  JupyterLab, JupyterLabPlugin
} from '@jupyterlab/application';

import * as qgrid from 'qgrid';

/**
 * The widget manager provider.
 */
const extension: JupyterLabPlugin<void> = {
  id: 'qgrid',
  autoStart: true,
  requires: [IJupyterWidgetRegistry],
  activate: function(app: JupyterLab, widgets: IJupyterWidgetRegistry) {

      widgets.registerWidget({
          name: 'qgrid',
          version: qgrid.version,
          exports: qgrid
      });
    }
};

export default extension;