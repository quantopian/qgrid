var qgrid = require('./index');

var base = require('@jupyter-widgets/base');

/**
 * The widget manager provider.
 */
module.exports = {
  id: 'qgrid',
  requires: [base.IJupyterWidgetRegistry],
  activate: function(app, widgets) {
      widgets.registerWidget({
          name: 'qgrid',
          version: qgrid.version,
          exports: qgrid
      });
    },
  autoStart: true
};
