var qgrid = require('qgrid');

var jupyterlab_widgets = require('@jupyter-widgets/jupyterlab-manager');

/**
 * The widget manager provider.
 */
module.exports = {
  id: 'qgrid',
  requires: [jupyterlab_widgets.INBWidgetExtension],
  activate: function(app, widgets) {
      widgets.registerWidget({
          name: 'qgrid',
          version: qgrid.version,
          exports: qgrid
      });
    },
  autoStart: true
};
