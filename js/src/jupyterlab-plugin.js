var ipyslickgrid = require('./index');

var base = require('@jupyter-widgets/base');

/**
 * The widget manager provider.
 */
module.exports = {
  id: 'ipyslickgrid',
  requires: [base.IJupyterWidgetRegistry],
  activate: function(app, widgets) {
      widgets.registerWidget({
          name: 'ipyslickgrid',
          version: ipyslickgrid.version,
          exports: ipyslickgrid
      });
    },
  autoStart: true
};
