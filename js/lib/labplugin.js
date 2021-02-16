var plugin = require('./index');
var base = require('@jupyter-widgets/base');

module.exports = {
  id: 'qgrid2:plugin',
  requires: [base.IJupyterWidgetRegistry],
  activate: function(app, widgets) {
      widgets.registerWidget({
          name: 'qgrid2',
          version: plugin.version,
          exports: plugin
      });
  },
  autoStart: true
};

