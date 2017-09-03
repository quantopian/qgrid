var widgets = require('@jupyter-widgets/base');
var _ = require('underscore');
var moment = require('moment');
window.jQuery = require('jquery');
var date_filter = require('./qgrid.datefilter.js');
var slider_filter = require('./qgrid.sliderfilter.js');
var text_filter = require('./qgrid.textfilter.js');
var boolean_filter = require('./qgrid.booleanfilter.js');
var editors = require('./qgrid.editors.js');
var calendar_icon = require('../lib/calendar.gif');
var checkmark_icon = require('../lib/tick.png');

require('slickgrid/slick.core.js');
require('slickgrid/lib/jquery.event.drag-2.3.0.js');
require('slickgrid/plugins/slick.rowselectionmodel.js');
require('slickgrid/plugins/slick.checkboxselectcolumn.js');
require('slickgrid/slick.dataview.js');
require('slickgrid/slick.grid.js');
require('slickgrid/slick.editors.js');
require('style-loader!slickgrid/slick.grid.css');
require('style-loader!slickgrid/slick-default-theme.css');
require('style-loader!jquery-ui/themes/base/minified/jquery-ui.min.css');
require('style-loader!./qgrid.css');

// Model for the qgrid widget
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


// View for the qgrid widget
class QgridView extends widgets.DOMWidgetView {
  render() {
    // subscribe to incoming messages from the QGridWidget
    this.model.on('msg:custom', this.handle_msg, this);
    this.initialize_qgrid();
  }

  /**
   * Main entry point for drawing the widget,
   * including toolbar buttons if necessary.
   */
  initialize_qgrid() {
    this.$el.empty();
    if (!this.$el.hasClass('q-grid-container')){
      this.$el.addClass('q-grid-container');
    }

    if (this.model.get('show_toolbar')) {
      this.initialize_toolbar();
    }

    this.initialize_slick_grid();
    //this.grid = new qgrid.QGrid(this.tableDiv, data_view, columns, this.model);
    //this.grid.initialize_slick_grid(options);
  }

  initialize_toolbar() {
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
      `).appendTo(this.toolbar);
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
        `);
      }

      this.in_progress_btn = clicked;
      clicked.text(clicked.attr('data-loading-text'));
      clicked.addClass('disabled');
      this.send({'type': clicked.attr('data-event-type')});
    });
  }

  /**
   * Create the grid portion of the widget, which is an instance of
   * SlickGrid, plus automatically created filter controls based on the
   * type of data in the columns of the DataFrame provided by the user.
   */
  initialize_slick_grid() {
    this.grid_elem = $("<div class='q-grid'>").appendTo(this.$el);

    // create the table
    var df_json = JSON.parse(this.model.get('_df_json'));
    var columns = this.model.get('_columns');
    this.data_view = this.create_data_view(df_json.data);
    var options = this.model.get('grid_options');

    this.columns = [];
    this.filters = {};
    this.filter_list = [];

    var number_type_info = {
      filter: slider_filter.SliderFilter,
      validator: editors.validateNumber,
      formatter: this.format_number
    };

    this.type_infos = {
      integer: Object.assign(
        { editor: Slick.Editors.Integer },
        number_type_info
      ),
      number: Object.assign(
        { editor: Slick.Editors.Float },
        number_type_info
      ),
      string: {
        filter: text_filter.TextFilter,
        editor: Slick.Editors.Text,
        formatter: this.format_string
      },
      datetime: {
        filter: date_filter.DateFilter,
        editor: Slick.Editors.Date,
        formatter: this.format_date
      },
      any: {
        filter: text_filter.TextFilter,
        editor: editors.SelectEditor,
        formatter: this.format_string
      },
      interval: {
        formatter: this.format_string
      },
      boolean: {
        filter: boolean_filter.BooleanFilter,
        editor: Slick.Editors.Checkbox,
        formatter: (row, cell, value, columngDef, dataContext) => {
          return value ? `<img src='${checkmark_icon}'>` : "";
        }
      }
    };

    $.datepicker.setDefaults({buttonImage: calendar_icon});

    $.each(columns, (i, cur_column) => {
      var type_info = this.type_infos[cur_column.type] || {};

      var slick_column = {
        name: cur_column.name,
        field: cur_column.name,
        id: cur_column.name,
        sortable: true,
        resizable: true,
        cssClass: cur_column.type
      };

      Object.assign(slick_column, type_info);

      if(cur_column.type == 'any'){
        slick_column.editorOptions = {
          options: cur_column.constraints.enum
        };
      }

      if (slick_column.filter){
        var cur_filter = new slick_column.filter(
            slick_column.field,
            cur_column.type,
            this
        );
        $(cur_filter).on("filter_changed", this.handle_filter_changed);
        $(cur_filter).on("viewport_changed", this.handle_filter_viewport_changed);
        $(cur_filter).on("get_column_min_max", this.handle_get_min_max);
        this.filters[slick_column.id] = cur_filter;
        this.filter_list.push(cur_filter);
      }

      this.columns.push(slick_column);
    });

    var row_count = 0;

    this.slick_grid = new Slick.Grid(
      this.grid_elem,
      this.data_view,
      this.columns,
      options
    );

    if (options.forceFitColumns){
      this.grid_elem.addClass('force-fit-columns');
    }

    setTimeout(() => {
      this.slick_grid.init();
      var max_height = options.height || options.rowHeight * 20;
      var grid_height = max_height;
      // totalRowHeight is how tall the grid would have to be to fit all of the rows in the dataframe.
      // The '+ 1' accounts for the height of the column header.
      var total_row_height = (this.data_view.getLength() + 1) * options.rowHeight + 1;
      if (total_row_height <= max_height){
        grid_height = total_row_height;
        this.grid_elem.addClass('hide-scrollbar');
      } else {
        this.grid_elem.removeClass('hide-scrollbar');
      }
      this.grid_elem.height(grid_height);
      this.slick_grid.resizeCanvas();
    }, 1);

    this.slick_grid.setSelectionModel(new Slick.RowSelectionModel());
    this.slick_grid.render();

    this.slick_grid.onHeaderCellRendered.subscribe((e, args) => {
      var cur_filter = this.filters[args.column.id];
      if (cur_filter){
        cur_filter.render_filter_button($(args.node), this.slick_grid);
      }
    });

    // Force the grid to re-render the column headers so the
    // onHeaderCellRendered event is triggered.
    this.slick_grid.setColumns(this.slick_grid.getColumns());

    $(window).resize(() => {
      this.slick_grid.resizeCanvas();
    });

    this.slick_grid.setSortColumns([]);

    this.slick_grid.onSort.subscribe((e, args) => {
      var msg = {
        'type': 'sort_changed',
        'sort_field': args.sortCol.field,
        'sort_ascending': args.sortAsc
      };
      this.send(msg);
    });

    this.slick_grid.onViewportChanged.subscribe((e) => {
      if (this.viewport_timeout){
        clearTimeout(this.viewport_timeout);
      }
      this.viewport_timeout = setTimeout(() => {
        var vp = this.slick_grid.getViewport();
        var msg = {'type': 'viewport_changed', 'top': vp.top, 'bottom': vp.bottom};
        this.send(msg);
        this.viewport_timeout = null;
      }, 100);
    });

    // set up callbacks
    this.slick_grid.onCellChange.subscribe((e, args) => {
      var column = df_json.schema.fields[args.cell].name;
      var id = this.slick_grid.getDataItem(args.row).slick_grid_id;
      var row = Number(id.replace('row', ''));
      var msg = {'row': row, 'column': column,
                 'value': args.item[column], 'type': 'cell_change'};
      this.send(msg);
    });

    this.slick_grid.onSelectedRowsChanged.subscribe((e, args) => {
      var msg = {'rows': args.rows, 'type': 'selection_change'};
      this.send(msg);
    });
  }

  has_active_filter() {
    for (var i=0; i < this.filter_list.length; i++){
      var cur_filter = this.filter_list[i];
      if (cur_filter.is_active()){
        return true;
      }
    }
    return false;
  }

  /**
   * Main entry point for drawing the widget,
   * including toolbar buttons if necessary.
   */
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

  set_data_view(data_view) {
    this.data_view = data_view;
    this.slick_grid.setData(data_view);
  }

  format_date(row, cell, value, columnDef, dataContext) {
    return moment.parseZone(value).format("YYYY-MM-DD");
  }

  format_string(row, cell, value, columnDef, dataContext) {
    return value;
  }

  format_number(row, cell, value, columnDef, dataContext) {
    return value;
  }

  handle_filter_viewport_changed(e, msg) {
    this.widget_model.send(msg);
  }

  /**
   * Handle messages from the QGridWidget.
   */
  handle_msg(msg) {
    if (msg.type === 'remove_row') {
      var cell = this.slick_grid.getActiveCell();
      if (!cell) {
          console.log('no cell');
          return;
      }
      var data = this.slick_grid.getData().getItem(cell.row);
      this.grid.data_view.deleteItem(data.slick_grid_id);
      var row = Number(data.slick_grid_id.replace('row', ''));
      msg = {'type': 'remove_row', 'row': row, 'id': data.id};
      this.updateSize();
      this.send(msg);

    } else if (msg.type === 'add_row') {
      var dd = this.slick_grid.getData();
      dd.addItem(msg);
      dd.refresh();
      this.updateSize();
      this.send(msg);
    } else if (msg.type === 'draw_table') {
      this.drawTable();
    } else if (msg.type == 'show_error') {
      alert(msg.error_msg);
      if (msg.triggered_by == 'add_row' ||
        msg.triggered_by == 'remove_row'){
        this.reset_in_progress_button();
      }
    } else if (msg.type == 'update_data_view') {
      if (this.update_timeout){
        clearTimeout(this.update_timeout);
      }
      this.update_timeout = setTimeout(() => {
        var df_json = JSON.parse(this.model.get('_df_json'));
        var data_view = this.create_data_view(df_json.data);

        let top_row = null;
        if (msg.triggered_by === 'remove_row'){
          top_row = this.slick_grid.getViewport().top;
        }

        this.set_data_view(data_view);
        this.slick_grid.render();

        if (msg.triggered_by !== 'filter_changed') {
          this.updateSize();
        }
        this.update_timeout = null;
        this.reset_in_progress_button();
        if (top_row) {
          this.slick_grid.scrollRowIntoView(top_row);
        } else if (msg.triggered_by === 'add_row') {
          let data_length = data_view.getLength();
          this.slick_grid.scrollRowIntoView(data_length);
          this.slick_grid.setSelectedRows([data_length - 1]);
        }

        var selected_rows = this.slick_grid.getSelectedRows().filter((row) => {
          return row < Math.min(this.df_length, this.df_range[1]);
        });
        this.send({
          'rows': selected_rows,
          'type': 'selection_change'
        });
      }, 100);
    } else if (msg.col_info) {
      var filter = this.filters[msg.col_info.name];
      filter.handle_msg(msg);
    }
  }

  reset_in_progress_button() {
    if (this.in_progress_btn){
      this.in_progress_btn.removeClass('disabled');
      this.in_progress_btn.text(
        this.in_progress_btn.attr('data-btn-text')
      );
      this.in_progress_btn = null;
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
      (this.data_view.getLength() + 1) * rowHeight + 1;
    if (total_row_height <= max_height){
      grid_height = Math.max(min_height, total_row_height);
      this.grid_elem.addClass('hide-scrollbar');
    } else {
      this.grid_elem.removeClass('hide-scrollbar');
    }
    this.grid_elem.height(grid_height);
    this.slick_grid.render();
    this.slick_grid.resizeCanvas();
  }
}

module.exports = {
  QgridModel : QgridModel,
  QgridView : QgridView
};
