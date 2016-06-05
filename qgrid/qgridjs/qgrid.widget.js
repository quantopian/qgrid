if (IPython.version[0] === '4' && parseInt(IPython.version[2]) >= 2) {
    var path = 'jupyter-js-widgets';
} else {
    var path = 'widgets/js/widget';
    if (IPython.version[0] !== '3') {
        path = 'nbextensions/widgets/' + path;
    }
}
define([path], function(widget) {

    var grid;
    var QGridView = widget.DOMWidgetView.extend({

        render: function() {
            var that = this;
            var cdn_base_url = this.model.get('_cdn_base_url');

            // Load the custom css
            if ($("#dg-css").length == 0){
                $("head").append([
                    "<link href='" + cdn_base_url + "/lib/slick.grid.css' rel='stylesheet'>",
                    "<link href='" + cdn_base_url + "/lib/slick-default-theme.css' rel='stylesheet'>",
                    "<link href='https://cdnjs.cloudflare.com/ajax/libs/jqueryui/1.10.4/css/jquery-ui.min.css' rel='stylesheet'>",
                    "<link id='dg-css' href='" + cdn_base_url + "/qgrid.css' rel='stylesheet'>"
                ]);
            }

            var path_dictionary = {
                jquery_drag: cdn_base_url + "/lib/jquery.event.drag-2.2",
                slick_core: cdn_base_url + "/lib/slick.core.2.2",
                slick_data_view: cdn_base_url + "/lib/slick.dataview.2.2",
                slick_check_box_column: cdn_base_url + "/lib/slick.checkboxselectcolumn",
                slick_row_selection_model: cdn_base_url + "/lib/slick.rowselectionmodel",
                slick_grid: cdn_base_url + "/lib/slick.grid.2.2",
                data_grid: cdn_base_url + "/qgrid",
                date_filter: cdn_base_url + "/qgrid.datefilter",
                text_filter: cdn_base_url + "/qgrid.textfilter",
                slider_filter: cdn_base_url + "/qgrid.sliderfilter",
                filter_base:  cdn_base_url + "/qgrid.filterbase",
                editors: cdn_base_url + "/qgrid.editors",
                handlebars: "https://cdnjs.cloudflare.com/ajax/libs/handlebars.js/2.0.0/handlebars.min"
            };

            var existing_config = require.s.contexts._.config;
            if (!existing_config.paths['underscore']){
                path_dictionary['underscore'] = "https://cdnjs.cloudflare.com/ajax/libs/underscore.js/1.7.0/underscore-min";
            }

            if (!existing_config.paths['moment']){
                path_dictionary['moment'] = "https://cdnjs.cloudflare.com/ajax/libs/moment.js/2.8.3/moment.min";
            }

            if (!existing_config.paths['jqueryui']){
                path_dictionary['jqueryui'] = "https://ajax.googleapis.com/ajax/libs/jqueryui/1.11.1/jquery-ui.min";
            }

            require.config({
                paths: path_dictionary
            });

            if (typeof jQuery === 'function') {
                define('jquery', function() { return jQuery; });
            }

            /**
             * Load the required scripts and create the grid.
             */
            require([
                'jquery',
                'jquery_drag',
                'slick_core',
                'slick_data_view',
                'slick_check_box_column',
                'slick_row_selection_model',
            ],
            function() {
                require(['slick_grid'], function() {
                    require(["data_grid", "editors"],function(dgrid, editors) {
                            that.setupTable(dgrid, editors);
                            that.drawTable();
                        }
                    );
                });
            });
        },

        /**
         * Set up the table div.
         */
        setupTable: function(dgrid, editors) {
            this.dgrid = dgrid;
            this.editors = editors;
            // subscribe to incoming messages from the QGridWidget
            this.model.on('msg:custom', this.handleMsg, this);

            // set up the divs and styles
            this.$el.addClass('q-grid-container');
            var table = this.$el.append('div');
            table.addClass('q-grid');
            this.tableDiv = table[0];

            // fill the portion of the widget area not in the prompt
            var parent = this.el.parentElement;
            while (parent.className !== 'widget-area') {
                parent = parent.parentElement;
            }
            var width = (parent.clientWidth - parent.childNodes[0].clientWidth);
            this.el.setAttribute("style", "max-width:" + String(width) + "px;");
        },

        /**
         * Set up our QGrid and event handlers.
         */
        drawTable: function() {
            var that = this;
            var editors = this.editors;

            // create the table
            var df = JSON.parse(this.model.get('_df_json'));
            var column_types = JSON.parse(this.model.get('_column_types_json'));
            var options = this.model.get('grid_options');
            grid = new this.dgrid.QGrid(this.tableDiv, df, column_types);
            grid.initialize_slick_grid(options);

            // set up editing
            var sgrid = grid.slick_grid;
            var columns = sgrid.getColumns();
            for (var i = 1; i < columns.length; i++) {
                if (column_types[i].categories) {
                    columns[i].editor = editors.SelectEditor;
                    var options = {options: column_types[i].categories};
                    columns[i].editorOptions = options;
                } else if (columns[i].type === 'date') {
                   columns[i].editor = editors.DateEditor;
                } else if (column_types[i]) {
                   columns[i].editor = editors.TextEditor;
                }
                if (columns[i].type === 'number') {
                   columns[i].validator = editors.validateNumber;
                }
            }
            sgrid.setColumns(columns);

            // set up callbacks
            sgrid.onCellChange.subscribe(function(e, args) {
                var column = columns[args.cell].name;
                var id = args.grid.getDataItem(args.row).slick_grid_id;
                var row = Number(id.replace('row', ''));
                var msg = {'row': row, 'column': column,
                           'value': args.item[column], 'type': 'cell_change'};
                that.send(msg);
            });

            sgrid.onSelectedRowsChanged.subscribe(function(e, args) {
                var rows = [];
                var grid = args.grid;
                for (var r = 0; r < args.rows.length; r++) {
                    var id = grid.getDataItem(args.rows[r]).slick_grid_id;
                    rows.push(Number(id.replace('row', '')));
                }
                var msg = {'rows': rows, 'type': 'selection_change'};
                that.send(msg);
            });
        },

        /**
         * Handle messages from the QGridWidget.
         */
        handleMsg: function(msg) {
            var sgrid = grid.slick_grid;
            if (msg.type === 'remove_row') {
                var cell = sgrid.getActiveCell();
                if (!cell) {
                    console.log('no cell');
                    return;
                }
                var data = sgrid.getData().getItem(cell.row);
                grid.data_view.deleteItem(data.slick_grid_id);
                var row = Number(data.slick_grid_id.replace('row', ''));
                msg = {'type': 'remove_row', 'row': row, 'id': data.id};
                this.updateSize();
                this.send(msg);

            } else if (msg.type === 'add_row') {
                var dd = sgrid.getData();
                dd.addItem(msg);
                dd.refresh();
                this.updateSize();
                this.send(msg);

            } else if (msg.type === 'draw_table') {
                this.drawTable();
                this.updateSize();
            }
        },

        /**
         * Update the size of the dataframe.
         */
        updateSize: function() {
          var rowHeight = 28;
          var max_height = rowHeight * 15;
          var grid_height = max_height;
          var total_row_height = (grid.row_data.length + 1) * rowHeight + 1;
          if (total_row_height <= max_height){
            grid_height = total_row_height;
            grid.grid_elem.addClass('hide-scrollbar');
          } else {
            grid.grid_elem.removeClass('hide-scrollbar');
          }
          grid.grid_elem.height(grid_height);
          grid.slick_grid.render();
          grid.slick_grid.resizeCanvas();
         }
    });

    return {QGridView: QGridView}
});
