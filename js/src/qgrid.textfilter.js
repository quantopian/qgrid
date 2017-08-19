define([
    'jquery',
    "underscore",
    'handlebars',
    './qgrid.filterbase.js',
    'jquery-ui'
], function ($, _, handlebars, filter_base) {
  "use strict";

  var TextFilter = function(field, column_type, widget_model){
    this.base = filter_base.FilterBase;
    this.base(field, column_type, widget_model);
  }
  TextFilter.prototype = new filter_base.FilterBase;

  TextFilter.prototype.get_filter_template = function(){
    return handlebars.compile(
      "<div class='text-filter grid-filter dropdown-menu {{type}}-filter'>" +
        "<h3 class='popover-title'>" +
          "<div class='dropdown-title'>Filter by {{name}}</div>" +
          "<i class='fa fa-times icon-remove close-button'/>" +
        "</h3>" +
        "<div class='dropdown-body'>" +
          "<div class='input-area'>" +
            "<input class='search-input' type='text'/>" +
          "</div>" +
          "<div class='text-filter-grid'/>" +
          "<div class='no-results hidden'>No results found.</div>" +
        "</div>" +
        "<div class='dropdown-footer'>" +
          "<a class='select-all-link' href='#'>Select All</a>"+
          "<a class='reset-link' href='#'>Reset</a>"+
        "</div>" +
      "</div>"
    );
  }

  TextFilter.prototype.update_min_max = function(col_info){
    this.values = col_info['values'];
    this.length = col_info['length'];
    this.value_range = col_info['value_range'];
    this.selected_rows = [];
    for (var i=0; i < col_info['selected_length']; i++){
      this.selected_rows.push(i);
    }
    this.ignore_selection_changed = true;
    $.proxy(this.base.prototype.show_filter.call(this), this);
    this.ignore_selection_changed = false;
  };

  TextFilter.prototype.update_data_view = function(col_info) {
    if (this.update_timeout){
        clearTimeout(this.update_timeout);
    }

    this.update_timeout = setTimeout(() => {
      this.values = col_info['values'];
      this.length = col_info['length'];
      this.value_range = col_info['value_range'];

      if (this.length === 0) {
        this.filter_elem.find('.no-results').removeClass('hidden');
        this.filter_grid_elem.addClass('hidden');
        return;
      }

      this.filter_elem.find('.no-results').addClass('hidden');
      this.filter_grid_elem.removeClass('hidden');
      this.ignore_selection_changed = true;
      this.update_slick_grid_data();
      this.filter_grid.setData(this.data_view);
      this.selected_rows = [];
      for (var i=0; i < col_info['selected_length']; i++){
        this.selected_rows.push(i);
        this.row_selection_model.setSelectedRows(this.selected_rows);
      }
      this.filter_grid.render();
      this.ignore_selection_changed = false;
    }, 100);
  };

  TextFilter.prototype.update_slick_grid_data = function() {
    this.grid_items = this.values.map(function(value, index){
      return {
        id: value,
        value: value
      }
    });
    var self = this;
    this.data_view = {
      getLength: function() {
        return self.length;
      },
      getItem: function(i) {
        var default_row = {
          id: 'row' + i,
          value: ''
        };
        if (i >= self.value_range[0] && i < self.value_range[1]){
          return self.grid_items[i - self.value_range[0]] || default_row;
        } else {
          return default_row;
        }
      }
    };
  };

  TextFilter.prototype.initialize_controls = function(){
    $.proxy(this.base.prototype.initialize_controls.call(this), this);
    this.filter_grid_elem = this.filter_elem.find(".text-filter-grid");
    this.search_string = "";

    this.update_slick_grid_data();

    this.sort_comparer = function(x, y){
      var x_value = x.value;
      var y_value = y.value;

      // selected row should be sorted to the top
      if (x.selected != y.selected){
        return x.selected ? -1 : 1;
      }

      return x_value > y_value ? 1 : -1;
    }

    var text_filter = function(item, args){
      if (this.search_string){
        if (item.value.toLowerCase().indexOf(this.search_string.toLowerCase()) == -1){
          return false;
        }
      }
      return true;
    }

    var row_formatter = function(row, cell, value, columnDef, dataContext){
      return "<span class='text-filter-value'>" + dataContext.value + "</span>";
    }

    var checkboxSelector = new Slick.CheckboxSelectColumn({
      cssClass: "check-box-cell"
    })

    var columns = [
      checkboxSelector.getColumnDefinition(),
      {
        id: "name",
        name: "Name",
        field: "name",
        formatter: row_formatter,
        sortable: true
      }];

    var options = {
      enableCellNavigation: true,
      fullWidthRows: true,
      syncColumnCellResize: true,
      rowHeight: 32,
      forceFitColumns: true,
      enableColumnReorder: false
    };

    var max_height = options.rowHeight * 8;
    // Subtract 110 from viewport height to account for the height of the header + search box + footer
    // of the filter control.  This value can't be calculated dynamically because the filter control
    // hasn't been shown yet.
    var qgrid_viewport_height = this.column_header_elem.closest('.slick-header').siblings('.slick-viewport').height() - 115;
    if (qgrid_viewport_height < max_height){
      max_height = qgrid_viewport_height;
    }

    var grid_height = max_height;
    // totalRowHeight is how tall the grid would have to be to fit all of the rows in the dataframe.
    var total_row_height = (this.grid_items.length) * options.rowHeight;

    if (total_row_height <= max_height){
      grid_height = total_row_height;
      this.filter_grid_elem.addClass('hide-scrollbar');
    }
    this.filter_grid_elem.height(grid_height);

    this.filter_grid = new Slick.Grid(this.filter_grid_elem, this.data_view,  columns, options);
    window.filter_grid = this.filter_grid;
    this.filter_grid.registerPlugin(checkboxSelector);

    this.row_selection_model = new Slick.RowSelectionModel({selectActiveRow: false});
    this.row_selection_model.onSelectedRangesChanged.subscribe($.proxy(this.handle_selection_changed, this));

    this.filter_grid.setSelectionModel(this.row_selection_model);
    this.row_selection_model.setSelectedRows(this.selected_rows);

    var that = this;

    if (this.column_type != 'any') {
      this.filter_grid.onViewportChanged.subscribe(function (e, args) {
        if (that.viewport_timeout) {
          clearTimeout(that.viewport_timeout);
        }
        that.viewport_timeout = setTimeout(function () {
          var vp = args.grid.getViewport();
          var msg = {
            'type': 'viewport_changed_filter',
            'field': that.field,
            'top': vp.top,
            'bottom': vp.bottom
          };
          $(that).trigger('viewport_changed', msg);
          that.viewport_timeout = null;
        }, 100);
      });
    }

    this.filter_grid.render();

    this.security_search = this.filter_elem.find(".search-input");
    this.security_search.keyup($.proxy(this.handle_text_input_key_up, this));
    this.security_search.click($.proxy(this.handle_text_input_click, this));

    this.filter_grid.onClick.subscribe($.proxy(this.handle_grid_clicked, this));
    this.filter_grid.onKeyDown.subscribe($.proxy(this.handle_grid_key_down, this));

    this.filter_elem.find("a.select-all-link").click($.proxy(function(e){
      this.ignore_selection_changed = true;
      this.reset_filter();
      this.filter_list = "all";
      var all_row_indices = [];
      for (var i=0; i< this.length; i++){
        all_row_indices.push(i)
      }
      this.row_selection_model.setSelectedRows(all_row_indices);
      this.ignore_selection_changed = false;
      $(this).trigger("filter_changed", this.get_filter_info());
      return false;
    }, this));

    var self =  this;
    setTimeout(function(){
      self.filter_grid.setColumns(self.filter_grid.getColumns());
      self.filter_grid.resizeCanvas();
    }, 10);

  }

  TextFilter.prototype.toggle_row_selected = function(row_index){
    var old_selected_rows = this.row_selection_model.getSelectedRows();
    // if the row is already selected, remove it from the selected rows array.
    var selected_rows = old_selected_rows.filter(function(word){
      return word !== row_index;
    });
    // otherwise add it to the selected rows array so it gets selected
    if (selected_rows.length == old_selected_rows.length){
      selected_rows.push(row_index);
    }
    this.row_selection_model.setSelectedRows(selected_rows);
  };

  TextFilter.prototype.handle_grid_clicked = function(e, args){
    this.toggle_row_selected(args.row);
    var active_cell = this.filter_grid.getActiveCell();
    if (!active_cell){
      e.stopImmediatePropagation();
    }
  };

  TextFilter.prototype.handle_grid_key_down = function(e, args){
    var active_cell = this.filter_grid.getActiveCell();
    if (active_cell){
      if (e.keyCode == 13){ // enter key
        this.toggle_row_selected(active_cell.row);
        return;
      }

      // focus on the search box for any key other than the up/down arrows
      if (e.keyCode != 40 && e.keyCode != 38){
        this.focus_on_search_box();
        return;
      }

      // also focus on the search box if we're at the top of the grid and this is the up arrow
      else if (active_cell.row == 0 && e.keyCode == 38){
        this.focus_on_search_box();
        e.preventDefault();
        return;
      }
    }
  }

  TextFilter.prototype.focus_on_search_box = function(){
    this.security_search.focus().val(this.search_string);
    this.filter_grid.resetActiveCell();
  }

  TextFilter.prototype.handle_text_input_key_up = function(e){
    var old_search_string = this.search_string;
    if (e.keyCode == 40){ // down arrow
      this.filter_grid.focus();
      this.filter_grid.setActiveCell(0, 0);
      return;
    }
    if (e.keyCode == 13){ // enter key
      if (this.security_grid.getDataLength() > 0){
        this.toggle_row_selected(0);
        this.security_search.val("");
      }
    }

    this.search_string = this.security_search.val();
    if (old_search_string != this.search_string){
      var msg = {
        'type': 'get_column_min_max',
        'field': this.field,
        'search_val': this.search_string
      };
      this.widget_model.send(msg)
    }
  };

  TextFilter.prototype.handle_text_input_click = function(e){
    this.filter_grid.resetActiveCell();
  };

  TextFilter.prototype.handle_selection_changed = function(e, args){
    if (this.ignore_selection_changed){
      return false;
    }

    var rows = this.row_selection_model.getSelectedRows();
    rows = _.sortBy(rows, function(i){ return i; });
    this.excluded_rows = [];
    var self = this;
    if (this.filter_list == 'all'){
      var j = 0;
      for(var i = 0; i < self.data_view.getLength(); i++){
        if (rows[j] == i){
          j += 1;
          continue;
        } else {
          this.excluded_rows.push(i);
        }
      }
    } else {
      this.filter_list = rows.length > 0 ? rows : null
    }

    $(this).trigger("filter_changed", this.get_filter_info());
  };

  TextFilter.prototype.is_active = function(){
    return this.filter_list != null;
  }

  TextFilter.prototype.reset_filter = function(){
    this.search_string = "";
    this.excluded_rows = null;
    this.security_search.val("");
    this.row_selection_model.setSelectedRows([]);
    this.filter_list = null;
  };

  TextFilter.prototype.get_filter_info = function(){
      return {
        "field": this.field,
        "type": "text",
        "selected": this.filter_list,
        "excluded": this.excluded_rows
      };
  };

  TextFilter.prototype.include_item = function(item){
    if (this.filter_list && !this.filter_list[item[this.field]]){
      return false;
    }
    return true;
  }

  return {'TextFilter': TextFilter}
});
