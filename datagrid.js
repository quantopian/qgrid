define([
    'jquery',
    "underscore",
    'moment',
    'date_filter',
    'slick_grid'
], function ($, _, moment, date_filter) {
  "use strict";

  var dependencies_loaded = false;
  var grids_to_initialize = []

  var DataGrid = function (grid_elem_selector, data_frame, column_types) {
    this.grid_elem_selector = grid_elem_selector;
    this.grid_elem = $(this.grid_elem_selector)
    this.data_frame = data_frame;

    this.row_data = [];
    this.columns = [];
    this.filters = {};
    this.filter_list = [];
    this.sort_field = "id";
    this.sort_ascending = true;

    this.python_types = {
      Character: "string",
      Float: "number",
      Complex: "number",
      Datetime: "date",
      Integer: "number",
      UnsignedInteger: "number"
    };

    var self = this;

    if (column_types.length > 0) {
      for (var i = 0; i < column_types.length; i++){
        var cur_column = column_types[i];

        if (!cur_column.type){
          cur_column.type = "string";
        }else{
          cur_column.type = this.python_types[cur_column.type];
        }

        if (i === 0){
          this.sort_field = cur_column.field;
        }

        cur_column = {
          name: cur_column.field,
          field: cur_column.field,
          id: cur_column.field,
          type: cur_column.type,
          formatter: this["format_" + cur_column.type],
          sortable: true,
          resizable: true
        };

        var filter_generator = this["create_" + cur_column.type + "_filter"];
        if (filter_generator){
          var cur_filter = filter_generator(cur_column.field);
          $(cur_filter).on("filter_changed", $.proxy(this.handle_filter_changed, this))
          this.filters[cur_column.id] = cur_filter;
          this.filter_list.push(cur_filter);
        }

        this.columns.push(cur_column);
      }
    }

    var row_count = 0;
    _.each(this.data_frame, function (cur_row, key, list) {
      cur_row.id = "row" + row_count;
      row_count++;
      this.row_data.push(cur_row);
      this.filter_list.forEach(function(cur_filter){
        cur_filter.handle_row_data(cur_row);
      }, this);
    }, this);
  }

  DataGrid.prototype.initialize_slick_grid = function () {
    this.data_view = new Slick.Data.DataView({
      inlineFilters: false,
      enableTextSelectionOnCells: true
    })

    this.data_view.beginUpdate();
    var sort_comparer = this.get_sort_comparer(this.sort_field, this.sort_ascending)
    this.data_view.sort(sort_comparer, this.sort_ascending);
    this.data_view.setItems(this.row_data);
    this.data_view.setFilter($.proxy(this.include_row, this));
    this.data_view.endUpdate();

    var options = {
      enableCellNavigation: true,
      fullWidthRows: true,
      syncColumnCellResize: true,
      forceFitColumns: true,
      rowHeight: 28,
      enableColumnReorder: false
    };

    this.slick_grid = new Slick.Grid(this.grid_elem_selector, this.data_view, this.columns, options);
    this.update_sort_indicators();
    this.slick_grid.render();

    this.slick_grid.onSort.subscribe($.proxy(this.handle_sort_changed, this));
    this.slick_grid.onHeaderCellRendered.subscribe($.proxy(this.handle_header_cell_rendered, this))

    // Force the grid to re-render the column headers so the onHeaderCellRendered event is triggered.
    this.slick_grid.setColumns(this.slick_grid.getColumns());

    var self = this;
    this.data_view.onRowCountChanged.subscribe(function(e, args){
      self.slick_grid.updateRowCount();
      self.slick_grid.render();
    });

    this.data_view.onRowsChanged.subscribe(function(e, args){
      self.slick_grid.invalidateRows(args.rows)
      self.slick_grid.render()
    });

    $(window).resize(function(){
      self.slick_grid.resizeCanvas();
    });
  }

  DataGrid.prototype.handle_filter_changed = function(e, exclude_this_filter){
    var show_clear_filter_button = false;
    for (var i=0; i < this.filter_list.length; i++){
      var cur_filter = this.filter_list[i];
      var filter_button = this.grid_elem.find(".slick-header-column." + cur_filter.field + "-header .filter-button");
      if (cur_filter.is_active()){
        show_clear_filter_button = true;
        filter_button.addClass("filter-active");
      }
      else {
        filter_button.removeClass("filter-active");
      }
    }
//    if (show_clear_filter_button){
//      this.tab_elem.find(".clear-filters").show();
//    }
//    else {
//      this.tab_elem.find(".clear-filters").hide();
//    }

    this.apply_filters(exclude_this_filter ? e.target : null)
  }

  DataGrid.prototype.apply_filters = function(excluded_filter){
//    for (var i=0; i < this.filters; i++){
//      if cur_filter instanceof quanto.SliderFilter  && cur_filter != excluded_filter
//        cur_filter.reset_min_max();
//    }
    this.data_view.refresh();
//    for (var i=0; i < this.filters; i++){
//      if cur_filter instanceof quanto.SliderFilter && cur_filter != excluded_filter
//        cur_filter.handle_filtering_done()
//    }
  }

  DataGrid.prototype.include_row = function(item, args){
    item.include = true;
    item.excluded_by = {};
    for (var i=0; i < this.filter_list.length; i++){
      var cur_filter = this.filter_list[i];
      if (!cur_filter.include_item(item)){
        item.include = false;
        item.excluded_by[cur_filter.field] = true;
      }
    }

//    for (var i=0; i < this.filters; i++){
//      if cur_filter instanceof quanto.SliderFilter
//        cur_filter.update_min_max(item)
//    }

    return item.include;
  }

  DataGrid.prototype.handle_sort_changed = function(e, args){
    this.sort_field = args.sortCol.field;
    this.sort_ascending = args.sortAsc;

    var sort_comparer = this.get_sort_comparer(this.sort_field, this.sort_ascending);
    this.data_view.sort(sort_comparer, this.sort_ascending);
  }

  DataGrid.prototype.update_sort_indicators = function(){
    this.slick_grid.setSortColumns([ {columnId: this.sort_field, sortAsc: this.sort_ascending} ]);
  }

  DataGrid.prototype.get_sort_comparer = function(field, ascending){
    return function(x, y){
      var x_value = x[field];
      var y_value = y[field];

      return (x_value > y_value) ? 1 : -1;
    }
  }

  DataGrid.prototype.handle_header_cell_rendered = function(e, args){
    var cur_filter = this.filters[args.column.id];
    if (cur_filter){
      $.proxy(cur_filter.render_filter_button($(args.node), this.slick_grid), cur_filter);
    }
  }

  DataGrid.prototype.format_date = function(row, cell, value, columnDef, dataContext){
    var date = new Date(value);
    return moment(date).format("YYYY-MM-DD");
  }

  DataGrid.prototype.format_string = function(row, cell, value, columnDef, dataContext){
    return value;
  }

  DataGrid.prototype.format_number = function(row, cell, value, columnDef, dataContext){
    return value;
  }

  DataGrid.prototype.create_date_filter = function(field){
    return new date_filter.DateFilter(field);
  }
//
//  DataGrid.prototype.create_number_filter = function(field){
//    return new quanto.SliderFilter(@$tab_elem, field);
//  }
//
//  DataGrid.prototype.create_money_filter = function(field){
//    return new quanto.SliderFilter(@$tab_elem, field, quanto.safe_to_money);
//  }
//
//  DataGrid.prototype.create_ticker_filter = function(field){
//    return new quanto.SecurityFilter(@$tab_elem, field);
//  }
//
//  DataGrid.prototype.create_text_filter = function(field){
//    return new quanto.TextFilter(@$tab_elem, field);
//  }

//  DataGrid.prototype.format_money = function(row, cell, value, columnDef, dataContext){
//    if (!value.value)
//      return "<span class='number no-value'>- -</span>";
//    else
//      return "<span class='number'>#{quanto.safe_to_money(value)}</span>";
//  }

//  DataGrid.prototype.format_total = function(totals, columnDef){
//    val = totals.sum.value ? totals.sum[columnDef.field] : null;
//    if (val.value)
//      return "<span class='number'><span class='total'>total:</span>#{quanto.safe_to_money(val)}</span>";
//    return "<span class='number no-value'>- -</span>";
//  }

  return { "DataGrid": DataGrid };

});
