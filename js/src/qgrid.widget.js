var widgets = require('jupyter-js-widgets');
var _ = require('underscore');
var slick_grid = require('slickgrid');
var qgrid = require('./qgrid.slickgrid.js');
var editors = require('./qgrid.editors.js');

// Custom Model. Custom widgets models must at least provide default values
// for model attributes, including
//
//  - `_view_name`
//  - `_view_module`
//  - `_view_module_version`
//
//  - `_model_name`
//  - `_model_module`
//  - `_model_module_version`
//
//  when different from the base class.

// When serialiazing the entire widget state for embedding, only values that
// differ from the defaults will be specified.
var QgridModel = widgets.DOMWidgetModel.extend({
    defaults: _.extend(_.result(this, 'widgets.DOMWidgetModel.prototype.defaults'), {
        _model_name : 'QgridModel',
        _view_name : 'QgridView',
        _model_module : 'qgrid',
        _view_module : 'qgrid',
        _model_module_version : '0.1.0',
        _view_module_version : '0.1.0',
        _df_json: '',

    })
});


// Custom View. Renders the widget model.
var QgridView = widgets.DOMWidgetView.extend({
    render: function() {
        // subscribe to incoming messages from the QGridWidget
        this.model.on('msg:custom', this.handleMsg, this);
        this.drawTable();
    },

    create_data_view: function() {
        var df = JSON.parse(this.model.get('_df_json'));
        var df_range = this.model.get("_df_range");
        var df_length = this.model.get("_row_count");
        return {
            getLength: function() {
                return df_length;
            },
            getItem: function(i) {
                if (i >= df_range[0] && i < df_range[1]){
                    var row = df[i - df_range[0]] || {};
                    row.slick_grid_id = "row" + i;
                    return row;
                } else {
                    return { slick_grid_id: "row" + i };
                }
            }
        };
    },

    /**
     * Set up our QGrid and event handlers.
     */
    drawTable: function() {
        var that = this;

        that.$el.empty();
        if (!that.$el.hasClass('q-grid-container')){
            this.$el.addClass('q-grid-container');
        }
        var table = this.$el.append('div');
        table.addClass('q-grid');
        that.tableDiv = table[0];

        // create the table
        var data_view = this.create_data_view();
        var column_types = this.model.get('_columns');
        var options = this.model.get('grid_options');
        grid = new qgrid.QGrid(this.tableDiv, data_view, column_types, that.model);
        grid.initialize_slick_grid(options);

        // set up editing
        var sgrid = grid.slick_grid;
        var columns = sgrid.getColumns();
        for (var i = 1; i < columns.length; i++) {
            var column_info = column_types[columns[i]['name']];
            var sgrid_column = columns[i];
            if (column_info.categories) {
                sgrid_column.editor = editors.SelectEditor;
                var options = {options: column_info.categories};
                sgrid_column.editorOptions = options;
            } else if (sgrid_column.type === 'date') {
               sgrid_column.editor = editors.DateEditor;
            } else if (column_types[i]) {
               sgrid_column.editor = editors.TextEditor;
            }
            if (sgrid_column.type === 'number') {
               sgrid_column.validator = editors.validateNumber;
            }
        }
        sgrid.setColumns(columns);
        sgrid.setSortColumns([]);

        sgrid.onSort.subscribe(function (e, args){
            var msg = {
                'type': 'sort_changed',
                'sort_field': args.sortCol.field,
                'sort_ascending': args.sortAsc
            };
            that.send(msg);
        });

        sgrid.onViewportChanged.subscribe(function (e, args) {
            if (that.viewport_timeout){
                clearTimeout(that.viewport_timeout);
            }
            that.viewport_timeout = setTimeout(function(){
                var vp = args.grid.getViewport();
                var msg = {'type': 'viewport_changed', 'top': vp.top, 'bottom': vp.bottom};
                that.send(msg);
                that.viewport_timeout = null;
            }, 100);
        });

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
        var that = this;
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
        } else if (msg.type == 'update_data_view') {
            if (that.update_timeout){
                clearTimeout(that.update_timeout);
            }
            that.update_timeout = setTimeout(function(){
                var data_view = that.create_data_view();
                sgrid.setData(data_view);
                sgrid.render();
                that.update_timeout = null;
            }, 100);
        }
    },

    /**
     * Update the size of the dataframe.
     */
    updateSize: function() {
        var rowHeight = 28;
        var max_height = rowHeight * 20;
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


module.exports = {
    QgridModel : QgridModel,
    QgridView : QgridView
};
