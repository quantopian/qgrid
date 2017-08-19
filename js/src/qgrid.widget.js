var widgets = require('@jupyter-widgets/base');
var _ = require('underscore');
window.jQuery = require('jquery');
var slick_grid = require('slickgrid');
var qgrid = require('./qgrid.slickgrid.js');

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
class QgridModel extends widgets.DOMWidgetModel {
    defaults() {
        return _.extend(widgets.DOMWidgetModel.prototype.defaults(), {
            _model_name : 'QgridModel',
            _view_name : 'QgridView',
            _model_module : 'qgrid',
            _view_module : 'qgrid',
            _model_module_version : '^1.0.0-alpha.6',
            _view_module_version : '^1.0.0-alpha.6',
            _df_json: '',
            _columns: {}
        });
    }
}


// Custom View. Renders the widget model.
class QgridView extends widgets.DOMWidgetView {
    render() {
        // subscribe to incoming messages from the QGridWidget
        this.model.on('msg:custom', this.handleMsg, this);
        this.drawTable();
    }

    create_data_view(df) {
        let df_range = this.df_range = this.model.get("_df_range");
        let df_length = this.df_length = this.model.get("_row_count");
        return {
            getLength: () => {
                return df_length;
            },
            getItem: (i) => {
                if (i >= df_range[0] && i < df_range[1]){
                    var row = df[i - df_range[0]] || {};
                    row.slick_grid_id = "row" + i;
                    return row;
                } else {
                    return { slick_grid_id: "row" + i };
                }
            }
        };
    }

    /**
     * Set up our QGrid and event handlers.
     */
    drawTable() {
        this.$el.empty();
        if (!this.$el.hasClass('q-grid-container')){
            this.$el.addClass('q-grid-container');
        }

        if (this.model.get('show_toolbar')) {
            this.$el.addClass('show-toolbar');
            this.toolbar = $("<div class='q-grid-toolbar'>").appendTo(this.$el);

            let append_btn = (btn_info) => {
                return $(`
                    <button
                    class='btn btn-default'
                    data-loading-text='${btn_info.loading_text}'
                    data-event-type='${btn_info.event_type}'
                    data-btn-text='${btn_info.text}'>
                        ${btn_info.text}
                    </button>
                `).appendTo(this.toolbar)
            };

            append_btn({
                loading_text: 'Adding...',
                event_type: 'add_row',
                text: 'Add Row'
            });

            append_btn({
                loading_text: 'Removing...',
                event_type: 'remove_row',
                text: 'Remove Row'
            });

            this.buttons = this.toolbar.find('.btn');

            this.buttons.click((e) => {
                let clicked = $(e.target);
                if (clicked.hasClass('disabled')){
                    return;
                }
                if (this.in_progress_btn){
                    alert(`
                        Adding/removing row is not available yet because the
                        previous operation is still in progress.
                    `)
                }

                this.in_progress_btn = clicked;
                clicked.text(clicked.attr('data-loading-text'));
                clicked.addClass('disabled');
                this.send({'type': clicked.attr('data-event-type')});
            });
        }

        var table = $("<div class='q-grid'>").appendTo(this.$el);
        this.tableDiv = table[0];

        // create the table
        var df_json = JSON.parse(this.model.get('_df_json'));
        var columns = this.model.get('_columns');
        var data_view = this.create_data_view(df_json.data);
        var options = this.model.get('grid_options');
        this.grid = new qgrid.QGrid(this.tableDiv, data_view, columns, this.model);
        this.grid.initialize_slick_grid(options);

        if (options['forceFitColumns']){
            table.addClass('force-fit-columns')
        }

        // set up editing
        var sgrid = this.grid.slick_grid;
        sgrid.setSortColumns([]);

        sgrid.onSort.subscribe((e, args) => {
            var msg = {
                'type': 'sort_changed',
                'sort_field': args.sortCol.field,
                'sort_ascending': args.sortAsc
            };
            this.send(msg);
        });

        sgrid.onViewportChanged.subscribe((e) => {
            if (this.viewport_timeout){
                clearTimeout(this.viewport_timeout);
            }
            this.viewport_timeout = setTimeout(() => {
                var vp = sgrid.getViewport();
                var msg = {'type': 'viewport_changed', 'top': vp.top, 'bottom': vp.bottom};
                this.send(msg);
                this.viewport_timeout = null;
            }, 100);
        });

        // set up callbacks
        sgrid.onCellChange.subscribe((e, args) => {
            var column = df_json.schema.fields[args.cell].name;
            var id = sgrid.getDataItem(args.row).slick_grid_id;
            var row = Number(id.replace('row', ''));
            var msg = {'row': row, 'column': column,
                       'value': args.item[column], 'type': 'cell_change'};
            this.send(msg);
        });

        sgrid.onSelectedRowsChanged.subscribe((e, args) => {
            var msg = {'rows': args.rows, 'type': 'selection_change'};
            this.send(msg);
        });
    }

    /**
     * Handle messages from the QGridWidget.
     */
    handleMsg(msg) {
        var sgrid = this.grid.slick_grid;
        if (msg.type === 'remove_row') {
            var cell = sgrid.getActiveCell();
            if (!cell) {
                console.log('no cell');
                return;
            }
            var data = sgrid.getData().getItem(cell.row);
            this.grid.data_view.deleteItem(data.slick_grid_id);
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
            if (this.update_timeout){
                clearTimeout(this.update_timeout);
            }
            this.update_timeout = setTimeout(() => {
                var df_json = JSON.parse(this.model.get('_df_json'));
                var data_view = this.create_data_view(df_json.data);

                let top_row = null;
                if (msg.triggered_by === 'remove_row'){
                    top_row = sgrid.getViewport().top;
                }

                this.grid.set_data_view(data_view);
                sgrid.render();

                if (msg.triggered_by !== 'filter_changed') {
                    this.updateSize();
                }
                this.update_timeout = null;
                if (this.in_progress_btn){
                    this.in_progress_btn.removeClass('disabled');
                    this.in_progress_btn.text(
                        this.in_progress_btn.attr('data-btn-text')
                    );
                    this.in_progress_btn = null;
                }
                if (top_row) {
                    sgrid.scrollRowIntoView(top_row);
                } else if (msg.triggered_by === 'add_row') {
                    let data_length = data_view.getLength();
                    sgrid.scrollRowIntoView(data_length);
                    sgrid.setSelectedRows([data_length - 1]);
                }

                var selected_rows = sgrid.getSelectedRows().filter((row) => {
                    return row < Math.min(this.df_length, this.df_range[1])
                });
                this.send({
                    'rows': selected_rows,
                    'type': 'selection_change'
                });
            }, 100);
        }
    }

    /**
     * Update the size of the dataframe.
     */
    updateSize() {
        var rowHeight = 28;
        var min_height = rowHeight * 8;
        var max_height = rowHeight * 20;
        var grid_height = max_height;
        var total_row_height =
            (this.grid.data_view.getLength() + 1) * rowHeight + 1;
        if (total_row_height <= max_height){
            grid_height = Math.max(min_height, total_row_height);
            this.grid.grid_elem.addClass('hide-scrollbar');
        } else {
            this.grid.grid_elem.removeClass('hide-scrollbar');
        }
        this.grid.grid_elem.height(grid_height);
        this.grid.slick_grid.render();
        this.grid.slick_grid.resizeCanvas();
    }
}


module.exports = {
    QgridModel : QgridModel,
    QgridView : QgridView
};
