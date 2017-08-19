define([
    'jquery',
    "underscore",
    'moment',
    './qgrid.datefilter.js',
    './qgrid.sliderfilter.js',
    './qgrid.textfilter.js',
    './qgrid.editors.js',
    'slickgrid/slick.core.js',
    'slickgrid/lib/jquery.event.drag-2.3.0.js',
    'slickgrid/slick.core.js',
    'slickgrid/plugins/slick.rowselectionmodel.js',
    'slickgrid/plugins/slick.checkboxselectcolumn.js',
    'slickgrid/slick.dataview.js',
    'slickgrid/slick.grid.js',
    'slickgrid/slick.editors.js',
    'style-loader!slickgrid/slick.grid.css',
    'style-loader!slickgrid/slick-default-theme.css',
    'style-loader!jquery-ui/themes/base/minified/jquery-ui.min.css',
    'style-loader!./qgrid.css',
], function ($, _, moment, date_filter, slider_filter, text_filter, editors) {
  "use strict";

  var dependencies_loaded = false;
  var grids_to_initialize = [];

  var QGrid = function (grid_elem_selector, data_view, columns, widget_model) {
    this.grid_elem_selector = grid_elem_selector;
    this.grid_elem = $(this.grid_elem_selector);
    this.data_view = data_view;
    this.widget_model = widget_model;
    this.widget_model.on('msg:custom', $.proxy(this.handle_msg, this), this);

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
      }
    };

    var self = this;
    $.each(columns, function(i, cur_column){
      var type_info = self.type_infos[cur_column.type] || {};

      var slick_column = {
        name: cur_column.name,
        field: cur_column.name,
        id: cur_column.name,
        sortable: true,
        resizable: true
      };

      Object.assign(slick_column, type_info);

      if(cur_column.type == 'any'){
        slick_column.editorOptions = {
          options: cur_column.constraints.enum
        };
      }

      if (slick_column.filter){
        var cur_filter = new slick_column.filter(slick_column.field, cur_column.type, self.widget_model);
        $(cur_filter).on("filter_changed", $.proxy(self.handle_filter_changed, self));
        $(cur_filter).on("viewport_changed", $.proxy(self.handle_filter_viewport_changed, self));
        $(cur_filter).on("get_column_min_max", $.proxy(self.handle_get_min_max, self));
        self.filters[slick_column.id] = cur_filter;
        self.filter_list.push(cur_filter);
      }

      self.columns.push(slick_column);
    });

    var row_count = 0;
    //_.each(this.data_frame, function (cur_row, key, list) {
    //  cur_row.slick_grid_id = "row" + row_count;
    //  row_count++;
    //  this.row_data.push(cur_row);
    //  this.filter_list.forEach(function(cur_filter){
    //    cur_filter.handle_row_data(cur_row);
    //  }, this);
    //}, this);
  };

  QGrid.prototype.format_date = function(row, cell, value, columnDef, dataContext){
    return moment.parseZone(value).format("YYYY-MM-DD");
  };

  QGrid.prototype.format_string = function(row, cell, value, columnDef, dataContext){
    return value;
  };

  QGrid.prototype.format_number = function(row, cell, value, columnDef, dataContext){
    return value;
  };

  QGrid.prototype.handle_msg = function(msg){
    if (msg.type == 'column_min_max_updated'){
      var column_info = msg.col_info;
      var filter = this.filters[column_info['name']];
      filter.update_min_max(column_info);
    } else if (msg.type == 'update_data_view_filter'){
      var column_info = msg.col_info;
      var filter = this.filters[column_info['name']];
      filter.update_data_view(column_info);
    }
  };

  QGrid.prototype.initialize_slick_grid = function (options) {
    var self = this;
    this.slick_grid = new Slick.Grid(
        this.grid_elem_selector,
        this.data_view,
        this.columns,
        options
    );

    window.slick_grid = this.slick_grid;

    setTimeout(function(){
      self.slick_grid.init();
      var max_height = options.height || options.rowHeight * 20;
      var grid_height = max_height;
      // totalRowHeight is how tall the grid would have to be to fit all of the rows in the dataframe.
      // The '+ 1' accounts for the height of the column header.
      var total_row_height = (self.data_view.getLength() + 1) * options.rowHeight + 1;
      if (total_row_height <= max_height){
        grid_height = total_row_height;
        self.grid_elem.addClass('hide-scrollbar');
      } else {
        self.grid_elem.removeClass('hide-scrollbar');
      }
      self.grid_elem.height(grid_height);
      self.slick_grid.resizeCanvas();
    }, 1);

    this.slick_grid.setSelectionModel(new Slick.RowSelectionModel());
    this.slick_grid.render();

    this.slick_grid.onHeaderCellRendered.subscribe($.proxy(this.handle_header_cell_rendered, this))

    // Force the grid to re-render the column headers so the onHeaderCellRendered event is triggered.
    this.slick_grid.setColumns(this.slick_grid.getColumns());

    //var self = this;
    //this.data_view.onRowCountChanged.subscribe(function(e, args){
    //  self.slick_grid.updateRowCount();
    //  self.slick_grid.render();
    //});
    //
    //this.data_view.onRowsChanged.subscribe(function(e, args){
    //  self.slick_grid.invalidateRows(args.rows)
    //  self.slick_grid.render()
    //});

    $(window).resize(function(){
      self.slick_grid.resizeCanvas();
    });
  };

  QGrid.prototype.set_data_view = function(data_view){
    this.data_view = data_view;
    this.slick_grid.setData(data_view);
  };

  QGrid.prototype.handle_filter_changed = function(e, filter_info){
    var show_clear_filter_button = false;

    for (var i=0; i < this.filter_list.length; i++){
      var cur_filter = this.filter_list[i];
      var filter_button = cur_filter.column_header_elem.find(".filter-button");
      if (cur_filter.is_active()){
        show_clear_filter_button = true;
        filter_button.addClass("filter-active");
      }
      else {
        filter_button.removeClass("filter-active");
      }
    }
    //if (show_clear_filter_button){
    //  this.tab_elem.find(".clear-filters").show();
    //}
    //else {
    //  this.tab_elem.find(".clear-filters").hide();
    //}

    var msg = {
      'type': 'filter_changed',
      'field': filter_info["field"],
      'filter_info': filter_info
    };
    this.widget_model.send(msg)
  };

  QGrid.prototype.handle_filter_viewport_changed = function(e, msg){
    this.widget_model.send(msg)
  };

  QGrid.prototype.handle_get_min_max = function(e, event_info) {
    var msg = {
        'type': 'get_column_min_max',
        'field': event_info.field,
        'search_val': event_info.search_val
    };
    this.widget_model.send(msg)
  };

  QGrid.prototype.apply_filters = function(excluded_filter){
    for (var i=0; i < this.filter_list.length; i++){
      var cur_filter = this.filter_list[i];
      if ((cur_filter instanceof slider_filter.SliderFilter)  && cur_filter != excluded_filter){
        cur_filter.reset_min_max();
      }
    }
    this.data_view.refresh();
    for (var i=0; i < this.filter_list.length; i++){
      var cur_filter = this.filter_list[i];
      if ((cur_filter instanceof slider_filter.SliderFilter) && cur_filter != excluded_filter){
        cur_filter.handle_filtering_done();
      }
    }
  }

  //QGrid.prototype.include_row = function(item, args){
  //  item.include = true;
  //  item.excluded_by = {};
  //  for (var i=0; i < this.filter_list.length; i++){
  //    var cur_filter = this.filter_list[i];
  //    if (!cur_filter.include_item(item)){
  //      item.include = false;
  //      item.excluded_by[cur_filter.field] = true;
  //    }
  //  }
  //
  //  for (var i=0; i < this.filter_list.length; i++){
  //    var cur_filter = this.filter_list[i];
  //    if (cur_filter instanceof slider_filter.SliderFilter){
  //      cur_filter.update_min_max(item);
  //    }
  //  }
  //
  //  return item.include;
  //}

  QGrid.prototype.handle_header_cell_rendered = function(e, args){
    var cur_filter = this.filters[args.column.id];
    if (cur_filter){
      $.proxy(cur_filter.render_filter_button($(args.node), this.slick_grid), cur_filter);
    }
  }



//
//  QGrid.prototype.create_ticker_filter = function(field){
//    return new quanto.SecurityFilter(@$tab_elem, field);
//  }
//
//  QGrid.prototype.format_money = function(row, cell, value, columnDef, dataContext){
//    if (!value.value)
//      return "<span class='number no-value'>- -</span>";
//    else
//      return "<span class='number'>#{quanto.safe_to_money(value)}</span>";
//  }

//  QGrid.prototype.format_total = function(totals, columnDef){
//    val = totals.sum.value ? totals.sum[columnDef.field] : null;
//    if (val.value)
//      return "<span class='number'><span class='total'>total:</span>#{quanto.safe_to_money(val)}</span>";
//    return "<span class='number no-value'>- -</span>";
//  }

  return { "QGrid": QGrid };

});
