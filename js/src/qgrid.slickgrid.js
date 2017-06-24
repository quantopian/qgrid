define([
    'jquery',
    "underscore",
    'moment',
    './qgrid.datefilter.js',
    './qgrid.sliderfilter.js',
    './qgrid.textfilter.js',
    './qgrid.editors.js',
    'slickgrid/lib/jquery.event.drag-2.3.0.js',
    'slickgrid/slick.core.js',
    'slickgrid/plugins/slick.rowselectionmodel.js',
    'slickgrid/plugins/slick.checkboxselectcolumn.js',
    'slickgrid/slick.dataview.js',
    'slickgrid/slick.grid.js',
    'style!slickgrid/slick.grid.css',
    'style!slickgrid/slick-default-theme.css',
    'style!jquery-ui/themes/base/minified/jquery-ui.min.css',
    'style!./qgrid.css',
], function ($, _, moment, date_filter, slider_filter, text_filter) {
  "use strict";

  var dependencies_loaded = false;
  var grids_to_initialize = [];

  var QGrid = function (grid_elem_selector, data_view, column_types) {
    this.grid_elem_selector = grid_elem_selector;
    this.grid_elem = $(this.grid_elem_selector);
    this.data_view = data_view;

    this.columns = [];
    this.filters = {};
    this.filter_list = [];

    this.python_types = {
      Character: "text",
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
          cur_column.type = "text";
        }else{
          cur_column.type = this.python_types[cur_column.type];
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
    //_.each(this.data_frame, function (cur_row, key, list) {
    //  cur_row.slick_grid_id = "row" + row_count;
    //  row_count++;
    //  this.row_data.push(cur_row);
    //  this.filter_list.forEach(function(cur_filter){
    //    cur_filter.handle_row_data(cur_row);
    //  }, this);
    //}, this);
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

  QGrid.prototype.handle_filter_changed = function(e, exclude_this_filter){
    var show_clear_filter_button = false;
    var filter_hash = {};

    //for (var i=0; i < this.filter_list.length; i++){
    //  var cur_filter = this.filter_list[i];
    //  var filter_button = cur_filter.column_header_elem.find(".filter-button");
    //  if (cur_filter.is_active()){
    //    show_clear_filter_button = true;
    //    filter_button.addClass("filter-active");
    //    filter_json
    //  }
    //  else {
    //    filter_button.removeClass("filter-active");
    //  }
    //}
//    if (show_clear_filter_button){
//      this.tab_elem.find(".clear-filters").show();
//    }
//    else {
//      this.tab_elem.find(".clear-filters").hide();
//    }

    //this.apply_filters(exclude_this_filter ? e.target : null)
  }

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

  QGrid.prototype.include_row = function(item, args){
    item.include = true;
    item.excluded_by = {};
    for (var i=0; i < this.filter_list.length; i++){
      var cur_filter = this.filter_list[i];
      if (!cur_filter.include_item(item)){
        item.include = false;
        item.excluded_by[cur_filter.field] = true;
      }
    }

    for (var i=0; i < this.filter_list.length; i++){
      var cur_filter = this.filter_list[i];
      if (cur_filter instanceof slider_filter.SliderFilter){
        cur_filter.update_min_max(item);
      }
    }

    return item.include;
  }

  QGrid.prototype.handle_header_cell_rendered = function(e, args){
    var cur_filter = this.filters[args.column.id];
    if (cur_filter){
      $.proxy(cur_filter.render_filter_button($(args.node), this.slick_grid), cur_filter);
    }
  }

  QGrid.prototype.format_date = function(row, cell, value, columnDef, dataContext){
    return moment.parseZone(value).format("YYYY-MM-DD");
  }

  QGrid.prototype.format_string = function(row, cell, value, columnDef, dataContext){
    return value;
  }

  QGrid.prototype.format_number = function(row, cell, value, columnDef, dataContext){
    return value;
  }

  QGrid.prototype.create_date_filter = function(field){
    return new date_filter.DateFilter(field);
  }

  QGrid.prototype.create_number_filter = function(field){
    return new slider_filter.SliderFilter(field);
  }

  QGrid.prototype.create_text_filter = function(field){
    return new text_filter.TextFilter(field);
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
