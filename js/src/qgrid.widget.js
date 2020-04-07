var widgets = require('@jupyter-widgets/base');
var _ = require('underscore');
var moment = require('moment');
window.$ = window.jQuery = require('jquery');
var date_filter = require('./qgrid.datefilter.js');
var slider_filter = require('./qgrid.sliderfilter.js');
var text_filter = require('./qgrid.textfilter.js');
var boolean_filter = require('./qgrid.booleanfilter.js');
var editors = require('./qgrid.editors.js');
var dialog = null;
try {
  dialog = require('base/js/dialog');
} catch (e) {
  console.warn("Qgrid was unable to load base/js/dialog. " +
               "Full screen button won't be available");
}
var jquery_ui = require('jquery-ui-dist/jquery-ui.min.js');

require('slickgrid-qgrid/slick.core.js');
require('slickgrid-qgrid/lib/jquery.event.drag-2.3.0.js');
require('slickgrid-qgrid/plugins/slick.rowselectionmodel.js');
require('slickgrid-qgrid/plugins/slick.checkboxselectcolumn.js');
require('slickgrid-qgrid/slick.dataview.js');
require('slickgrid-qgrid/slick.grid.js');
require('slickgrid-qgrid/slick.editors.js');
require('style-loader!slickgrid-qgrid/slick.grid.css');
require('style-loader!slickgrid-qgrid/slick-default-theme.css');
require('style-loader!jquery-ui-dist/jquery-ui.min.css');
require('style-loader!./qgrid.css');

// Model for the qgrid widget
class QgridModel extends widgets.DOMWidgetModel {
  defaults() {
    return _.extend(widgets.DOMWidgetModel.prototype.defaults(), {
      _model_name : 'QgridModel',
      _view_name : 'QgridView',
      _model_module : 'qgrid',
      _view_module : 'qgrid',
      _model_module_version : '^1.1.2',
      _view_module_version : '^1.1.2',
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
    this.initialize_toolbar();
    this.initialize_slick_grid();
  }

  initialize_toolbar() {
    if (!this.model.get('show_toolbar')){
      this.$el.removeClass('show-toolbar');
    } else {
      this.$el.addClass('show-toolbar');
    }

    if (this.toolbar){
      return;
    }

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
    this.buttons.attr('title',
        'Not available while there is an active filter');
    this.buttons.tooltip();
    this.buttons.tooltip({
      show: {delay: 300}
    });
    this.buttons.tooltip({
      hide: {delay: 100, 'duration': 0}
    });
    this.buttons.tooltip('disable');

    this.full_screen_btn = null;
    if (dialog) {
      this.full_screen_modal = $('body').find('.qgrid-modal');
      if (this.full_screen_modal.length == 0) {
        this.full_screen_modal = $(`
          <div class="modal qgrid-modal">
            <div class="modal-dialog">
              <div class="modal-content">
                <div class="modal-body"></div>
              </div>
            </div>
          </div>
        `).appendTo($('body'));
      }
      this.full_screen_btn = $(`
        <button
          class='btn btn-default fa fa-arrows-alt full-screen-btn'/>
      `).appendTo(this.toolbar);
      this.close_modal_btn = $(`
        <button
          class='btn btn-default fa fa-times close-modal-btn'
          data-dismiss="modal"/>
      `).appendTo(this.toolbar);

    }
    this.bind_toolbar_events();
  }

  bind_toolbar_events() {
    this.buttons.off('click');
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
    if (!this.full_screen_btn) {
      return;
    }
    this.full_screen_btn.off('click');
    this.full_screen_btn.click((e) => {
      this.$el_wrapper = this.$el.parent();
      this.$el_wrapper.height(this.$el_wrapper.height());
      this.$el.detach();
      var modal_options = {
        body: this.$el[0],
        show: false
      };
      if (IPython && IPython.keyboard_manager) {
        modal_options.keyboard_manager = IPython.keyboard_manager;
      }
      var qgrid_modal = dialog.modal(modal_options);

      qgrid_modal.removeClass('fade');
      qgrid_modal.addClass('qgrid-modal');
      qgrid_modal.on('shown.bs.modal', (e) => {
        this.slick_grid.resizeCanvas();
      });
      qgrid_modal.on('hidden.bs.modal', (e) => {
        this.$el.detach();
        this.$el_wrapper.height('auto');
        this.$el_wrapper.append(this.$el);
        this.update_size();
        this.slick_grid.bindAllEvents();
        this.bind_toolbar_events();
      });
      qgrid_modal.modal('show');
    });
  }

  /**
   * Create the grid portion of the widget, which is an instance of
   * SlickGrid, plus automatically created filter controls based on the
   * type of data in the columns of the DataFrame provided by the user.
   */
  initialize_slick_grid() {

    if (!this.grid_elem) {
      this.grid_elem = $("<div class='q-grid'>").appendTo(this.$el);
    }

    // create the table
    var df_json = JSON.parse(this.model.get('_df_json'));
    var columns = this.model.get('_columns');
    this.data_view = this.create_data_view(df_json.data);
    this.grid_options = this.model.get('grid_options');
    this.index_col_name = this.model.get("_index_col_name");
    this.row_styles = this.model.get("_row_styles");

    this.columns = [];
    this.index_columns = [];
    this.filters = {};
    this.filter_list = [];
    this.date_formats = {};
    this.last_vp = null;
    this.sort_in_progress = false;
    this.sort_indicator = null;
    this.resizing_column = false;
    this.ignore_selection_changed = false;
    this.vp_response_expected = false;
    this.next_viewport_msg = null;

    var number_type_info = {
      filter: slider_filter.SliderFilter,
      validator: editors.validateNumber,
      formatter: this.format_number
    };

    var self = this;

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
        editor: class DateEditor extends Slick.Editors.Date {
          constructor(args) {
            super(args);

            this.loadValue = (item) => {
              this.date_value = item[args.column.field];
              var formatted_val = self.format_date(
                  this.date_value, args.column.field
              );
              this.input = $(args.container).find('.editor-text');
              this.input.val(formatted_val);
              this.input[0].defaultValue = formatted_val;
              this.input.select();
              this.input.on("keydown.nav", function (e) {
                if (e.keyCode === $.ui.keyCode.LEFT || e.keyCode === $.ui.keyCode.RIGHT) {
                  e.stopImmediatePropagation();
                }
              });
            };

            this.isValueChanged = () => {
              return this.input.val() != this.date_value;
            };

            this.serializeValue = () => {
              if (this.input.val() === "") {
                  return null;
              }
              var parsed_date = moment.parseZone(
                  this.input.val(), "YYYY-MM-DD HH:mm:ss.SSS"
              );
              return parsed_date.format("YYYY-MM-DDTHH:mm:ss.SSSZ");
            };
          }
        },
        formatter: (row, cell, value, columnDef, dataContext) => {
          if (value === null){
            return "NaT";
          }
          return this.format_date(value, columnDef.name);
        }
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
          return value ? `<span class="fa fa-check"/>` : "";
        }
      }
    };

    $.datepicker.setDefaults({
      gotoCurrent: true,
      dateFormat: $.datepicker.ISO_8601,
      constrainInput: false,
      "prevText": "",
      "nextText": ""
    });

    var sorted_columns = Object.values(columns).sort(
        (a, b) => a.position - b.position
    );

    for(let cur_column of sorted_columns){
      if (cur_column.name == this.index_col_name){
        continue;
      }

      var type_info = this.type_infos[cur_column.type] || {};

      var slick_column = cur_column;

      Object.assign(slick_column, type_info);

      if (cur_column.type == 'any'){
        slick_column.editorOptions = {
          options: cur_column.constraints.enum
        };
      }

      if (slick_column.filter) {
        var cur_filter = new slick_column.filter(
            slick_column.field,
            cur_column.type,
            this
        );
        this.filters[slick_column.id] = cur_filter;
        this.filter_list.push(cur_filter);
      }

      if (cur_column.width == null){
        delete slick_column.width;
      }

      if (cur_column.maxWidth == null){
        delete slick_column.maxWidth;
      }

      // don't allow editing index columns
      if (cur_column.is_index) {
        slick_column.editor = editors.IndexEditor;
        
        if (cur_column.first_index){
          slick_column.cssClass += ' first-idx-col';
        }
        if (cur_column.last_index){
          slick_column.cssClass += ' last-idx-col';
        }

        slick_column.name = cur_column.index_display_text;
        slick_column.level = cur_column.level;

        if (this.grid_options.boldIndex) {
            slick_column.cssClass += ' idx-col';
        }

        this.index_columns.push(slick_column);
        continue;
      }

      if (cur_column.editable == false) {
        slick_column.editor = null;
      }

      this.columns.push(slick_column);
    }

    if (this.index_columns.length > 0) {
      this.columns = this.index_columns.concat(this.columns);
    }

    var row_count = 0;

    // set window.slick_grid for easy troubleshooting in the js console
    window.slick_grid = this.slick_grid = new Slick.Grid(
      this.grid_elem,
      this.data_view,
      this.columns,
      this.grid_options
    );
    this.grid_elem.data('slickgrid', this.slick_grid);

    if (this.grid_options.forceFitColumns){
      this.grid_elem.addClass('force-fit-columns');
    }

    if (this.grid_options.highlightSelectedCell) {
      this.grid_elem.addClass('highlight-selected-cell');
    }

    // compare to false since we still want to show row
    // selection if this option is excluded entirely
    if (this.grid_options.highlightSelectedRow != false) {
      this.grid_elem.addClass('highlight-selected-row');
    }

    setTimeout(() => {
      this.slick_grid.init();
      this.update_size();
    }, 1);

    this.slick_grid.setSelectionModel(new Slick.RowSelectionModel());
    this.slick_grid.setCellCssStyles("grouping", this.row_styles);
    this.slick_grid.render();
    
    this.update_size();

    var render_header_cell = (e, args) => {
      var cur_filter = this.filters[args.column.id];
        if (cur_filter) {
          cur_filter.render_filter_button($(args.node), this.slick_grid);
        }
    };

    if (this.grid_options.filterable != false) {
      this.slick_grid.onHeaderCellRendered.subscribe(render_header_cell);
    }

    // Force the grid to re-render the column headers so the
    // onHeaderCellRendered event is triggered.
    this.slick_grid.setColumns(this.slick_grid.getColumns());

    $(window).resize(() => {
      this.slick_grid.resizeCanvas();
    });

    this.slick_grid.setSortColumns([]);

    this.grid_header = this.$el.find('.slick-header-columns');
    var handle_header_click = (e) => {
      if (this.resizing_column) {
        return;
      }

      if (this.sort_in_progress){
        return;
      }

      var col_header = $(e.target).closest(".slick-header-column");
      if (!col_header.length) {
        return;
      }

      var column = col_header.data("column");
      if (column.sortable == false){
        return;
      }

      this.sort_in_progress = true;

      if (this.sorted_column == column){
        this.sort_ascending = !this.sort_ascending;
      } else {
        this.sorted_column = column;
        if ('defaultSortAsc' in column) {
          this.sort_ascending = column.defaultSortAsc;
        } else{
          this.sort_ascending = true;
        }
      }

      var all_classes = 'fa-sort-asc fa-sort-desc fa fa-spin fa-spinner';
      var clicked_column_sort_indicator = col_header.find('.slick-sort-indicator');
      if (clicked_column_sort_indicator.length == 0){
        clicked_column_sort_indicator =
            $("<span class='slick-sort-indicator'/>").appendTo(col_header);
      }

      this.sort_indicator = clicked_column_sort_indicator;
      this.sort_indicator.removeClass(all_classes);
      this.grid_elem.find('.slick-sort-indicator').removeClass(all_classes);
      this.sort_indicator.addClass(`fa fa-spinner fa-spin`);
      var msg = {
        'type': 'change_sort',
        'sort_field': this.sorted_column.field,
        'sort_ascending': this.sort_ascending
      };
      this.send(msg);
    };

    if (this.grid_options.sortable != false) {
      this.grid_header.click(handle_header_click)
    }

    this.slick_grid.onViewportChanged.subscribe((e) => {
      if (this.viewport_timeout){
        clearTimeout(this.viewport_timeout);
      }
      this.viewport_timeout = setTimeout(() => {
        this.last_vp = this.slick_grid.getViewport();
        var cur_range = this.model.get('_viewport_range');

        if (this.last_vp.top != cur_range[0] || this.last_vp.bottom != cur_range[1]) {
          var msg = {
            'type': 'change_viewport',
            'top': this.last_vp.top,
            'bottom': this.last_vp.bottom
          };
          if (this.vp_response_expected){
            this.next_viewport_msg = msg
          } else {
            this.vp_response_expected = true;
            this.send(msg);
          }
        }
        this.viewport_timeout = null;
      }, 100);
    });

    // set up callbacks
    let editable_rows = this.model.get('_editable_rows');
    if (editable_rows && Object.keys(editable_rows).length > 0) {
      this.slick_grid.onBeforeEditCell.subscribe((e, args) => {
        editable_rows = this.model.get('_editable_rows');
        return editable_rows[args.item[this.index_col_name]]
      });
    }

    this.slick_grid.onCellChange.subscribe((e, args) => {
      var column = this.columns[args.cell].name;
      var data_item = this.slick_grid.getDataItem(args.row);
      var msg = {'row_index': data_item.row_index, 'column': column,
                 'unfiltered_index': data_item[this.index_col_name],
                 'value': args.item[column], 'type': 'edit_cell'};
      this.send(msg);
    });

    this.slick_grid.onSelectedRowsChanged.subscribe((e, args) => {
      if (!this.ignore_selection_changed) {
        var msg = {'rows': args.rows, 'type': 'change_selection'};
        this.send(msg);
      }
    });

    setTimeout(() => {
      this.$el.closest('.output_wrapper')
          .find('.out_prompt_overlay,.output_collapsed').click(() => {
        setTimeout(() => {
          this.slick_grid.resizeCanvas();
        }, 1);
      });

      this.resize_handles = this.grid_header.find('.slick-resizable-handle');
      this.resize_handles.mousedown((e) => {
        this.resizing_column = true;
      });
      $(document).mouseup(() => {
        // wait for the column header click handler to run before
        // setting the resizing_column flag back to false
        setTimeout(() => {
          this.resizing_column = false;
        }, 1);
      });
    }, 1);
  }

  processPhosphorMessage(msg) {
    super.processPhosphorMessage(msg)
    switch (msg.type) {
    case 'resize':
    case 'after-show':
      if (this.slick_grid){
        this.slick_grid.resizeCanvas();
      }
      break;
    }
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
          row.row_index = i;
          return row;
        } else {
          return { row_index: i };
        }
      }
    };
  }

  set_data_view(data_view) {
    this.data_view = data_view;
    this.slick_grid.setData(data_view);
  }

  format_date(date_string, col_name) {
    if (!date_string) {
      return "";
    }
    var parsed_date = moment.parseZone(date_string, "YYYY-MM-DDTHH:mm:ss.SSSZ");
    var date_format = null;
    if (parsed_date.millisecond() != 0){
       date_format = `YYYY-MM-DD HH:mm:ss.SSS`;
    } else if (parsed_date.second() != 0){
      date_format = "YYYY-MM-DD HH:mm:ss";
    } else if (parsed_date.hour() != 0 || parsed_date.minute() != 0) {
      date_format = "YYYY-MM-DD HH:mm";
    } else {
      date_format = "YYYY-MM-DD";
    }

    if (col_name in this.date_formats){
      var old_format = this.date_formats[col_name];
      if (date_format.length > old_format.length){
        this.date_formats[col_name] = date_format;
        setTimeout(() => {
          this.slick_grid.invalidateAllRows();
          this.slick_grid.render();
        }, 1);
      } else {
        date_format = this.date_formats[col_name];
      }
    } else {
      this.date_formats[col_name] = date_format;
    }

    return parsed_date.format(date_format);
  }

  format_string(row, cell, value, columnDef, dataContext) {
    return value;
  }

  format_number(row, cell, value, columnDef, dataContext) {
    if (value === null){
      return 'NaN';
    }
    return value;
  }

  /**
   * Handle messages from the QGridWidget.
   */
  handle_msg(msg) {
    if (msg.type === 'draw_table') {
      this.initialize_slick_grid();
    } else if (msg.type == 'show_error') {
      alert(msg.error_msg);
      if (msg.triggered_by == 'add_row' ||
        msg.triggered_by == 'remove_row'){
        this.reset_in_progress_button();
      }
    } else if (msg.type == 'update_data_view') {
      if (this.buttons) {
        if (this.has_active_filter()) {
          this.buttons.addClass('disabled');
          this.buttons.tooltip('enable');
        } else if (this.buttons.hasClass('disabled')) {
          this.buttons.removeClass('disabled');
          this.buttons.tooltip('disable');
        }
      }
      if (this.update_timeout) {
        clearTimeout(this.update_timeout);
      }
      this.update_timeout = setTimeout(() => {
        var df_json = JSON.parse(this.model.get('_df_json'));
        this.row_styles = this.model.get("_row_styles");
        this.multi_index = this.model.get("_multi_index");
        var data_view = this.create_data_view(df_json.data);

        if (msg.triggered_by === 'change_viewport') {
          if (this.next_viewport_msg) {
            this.send(this.next_viewport_msg);
            this.next_viewport_msg = null;
            return;
          } else {
            this.vp_response_expected = false;
          }
        }

        if (msg.triggered_by == 'change_sort' && this.sort_indicator) {
          var asc = this.model.get('_sort_ascending');
          this.sort_indicator.removeClass(
              'fa-spinner fa-spin fa-sort-asc fa-sort-desc'
          );
          var fa_class = asc ? 'fa-sort-asc' : 'fa-sort-desc';
          this.sort_indicator.addClass(fa_class);
          this.sort_in_progress = false;
        }

        let top_row = null;
        if (msg.triggered_by === 'remove_row') {
          top_row = this.slick_grid.getViewport().top;
        }

        this.set_data_view(data_view);

        var skip_grouping = false;
        if (this.multi_index) {
          for (var i = 1; i < this.filter_list.length; i++) {
            var cur_filter = this.filter_list[i];
            if (cur_filter.is_active()) {
              skip_grouping = true;
            }
          }
        }

        if (skip_grouping) {
          this.slick_grid.removeCellCssStyles("grouping");
        } else {
          this.slick_grid.setCellCssStyles("grouping", this.row_styles);
        }

        this.slick_grid.render();

        if ((msg.triggered_by == 'add_row' ||
            msg.triggered_by == 'remove_row') && !this.has_active_filter()) {
          this.update_size();
        }
        this.update_timeout = null;
        this.reset_in_progress_button();
        if (top_row) {
          this.slick_grid.scrollRowIntoView(top_row);
        } else if (msg.triggered_by === 'add_row') {
          this.slick_grid.scrollRowIntoView(msg.scroll_to_row);
          this.slick_grid.setSelectedRows([msg.scroll_to_row]);
        } else if (msg.triggered_by === 'change_viewport' &&
            this.last_vp.bottom >= this.df_length) {
          this.slick_grid.scrollRowIntoView(this.last_vp.bottom);
        }

        var selected_rows = this.slick_grid.getSelectedRows().filter((row) => {
          return row < Math.min(this.df_length, this.df_range[1]);
        });
        this.send({
          'rows': selected_rows,
          'type': 'change_selection'
        });
      }, 100);
    } else if (msg.type == 'change_grid_option') {
      var opt_name = msg.option_name;
      var opt_val = msg.option_value;
      if (this.slick_grid.getOptions()[opt_name] != opt_val) {
        this.slick_grid.setOptions({[opt_name]: opt_val});
        this.slick_grid.resizeCanvas();
      }
    } else if (msg.type == 'change_selection') {
      this.ignore_selection_changed = true;
      this.slick_grid.setSelectedRows(msg.rows);
      if (msg.rows && msg.rows.length > 0) {
        this.slick_grid.scrollRowIntoView(msg.rows[0]);
      }
      this.ignore_selection_changed = false;
    } else if (msg.type == 'change_show_toolbar') {
      this.initialize_toolbar();
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
  update_size() {
    var row_height = this.grid_options.rowHeight;
    var min_visible = 'minVisibleRows' in this.grid_options ?
        this.grid_options.minVisibleRows : 8;
    var max_visible = 'maxVisibleRows' in this.grid_options ?
        this.grid_options.maxVisibleRows : 15;

    var min_height = row_height * min_visible;
    // add 2 to maxVisibleRows to account for the header row and padding
    var max_height = 'height' in this.grid_options ? this.grid_options.height :
      row_height * (max_visible + 2);
    var grid_height = max_height;
    var total_row_height = (this.data_view.getLength() + 1) * row_height + 1;
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
