/*
 * Modifications copyright (C) 2021 8080 Labs GmbH
 *
 * - replaced qgrid with ipyslickgrid in lines 14, 18, 19, 20
 */

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
