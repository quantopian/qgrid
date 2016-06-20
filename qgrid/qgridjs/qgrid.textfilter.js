define([
    'jquery',
    "underscore",
    'handlebars',
    'filter_base',
    'jqueryui'
], function ($, _, handlebars, filter_base) {
  "use strict";

  var TextFilter = function(field){
    this.base = filter_base.FilterBase;
    this.base(field);
    this.items_hash = {};
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
        "</div>" +
        "<div class='dropdown-footer'>" +
          "<a class='select-all-link' href='#'>Select All</a>"+
          "<a class='reset-link' href='#'>Reset</a>"+
        "</div>" +
      "</div>"
    );
  }

  TextFilter.prototype.initialize_min_max = function(item){
    $.proxy(this.base.prototype.initialize_min_max.call(this, item), this);
    var item_value = item[this.field];
    this.items_hash[item_value] = {id: item_value, value: item_value}
  }

  TextFilter.prototype.initialize_controls = function(){
    $.proxy(this.base.prototype.initialize_controls.call(this), this);
    this.filter_grid_elem = this.filter_elem.find(".text-filter-grid");
    this.search_string = "";

    this.grid_items = _.values(this.items_hash);

    this.data_view = new Slick.Data.DataView({
      inlineFilters: false,
      enableTextSelectionOnCells: true
    });

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

    this.data_view.beginUpdate();
    this.data_view.setItems(this.grid_items);
    this.data_view.setFilter($.proxy(text_filter, this));
    this.data_view.sort($.proxy(this.sort_comparer, this), true);
    this.data_view.endUpdate();

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
    this.filter_grid.registerPlugin(checkboxSelector);

    this.row_selection_model = new Slick.RowSelectionModel({selectActiveRow: false});
    this.row_selection_model.onSelectedRangesChanged.subscribe($.proxy(this.handle_selection_changed, this));

    this.filter_grid.setSelectionModel(this.row_selection_model);
    this.data_view.syncGridSelection(this.filter_grid, true, true);
    this.filter_grid.render();

    this.data_view.onRowCountChanged.subscribe($.proxy(function(e, args){
      this.filter_grid.updateRowCount();
      this.filter_grid.render();
    }, this));

    this.data_view.onRowsChanged.subscribe($.proxy(function(e, args){
      this.filter_grid.invalidateRows(args.rows);
      this.filter_grid.render();
    }, this));

    this.security_search = this.filter_elem.find(".search-input");
    this.security_search.keyup($.proxy(this.handle_text_input_key_up, this));
    this.security_search.click($.proxy(this.handle_text_input_click, this));

    this.filter_grid.onClick.subscribe($.proxy(this.handle_grid_clicked, this));
    this.filter_grid.onKeyDown.subscribe($.proxy(this.handle_grid_key_down, this));

    this.filter_elem.find("a.select-all-link").click($.proxy(function(e){
      this.reset_filter();
      var all_row_indices = [];
      var all_rows = this.data_view.getItems();
      for (var i=0; i< all_rows.length; i++){
        all_row_indices.push(i)
      }
      this.row_selection_model.setSelectedRows(all_row_indices);
      $(this).trigger("filter_changed");
      return false;
    }, this));
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
  }

  TextFilter.prototype.handle_grid_clicked = function(e, args){
    this.toggle_row_selected(args.row);
    var active_cell = this.filter_grid.getActiveCell();
    if (!active_cell){
      e.stopImmediatePropagation();
    }
  }

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

  TextFilter.prototype.sort_if_needed = function(force){
    if (force || this.sort_needed){
      this.data_view.sort(this.sort_comparer, true);
      this.sort_needed = false;
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
      this.data_view.refresh();
      this.sort_if_needed();
    }
  }

  TextFilter.prototype.handle_text_input_click = function(e){
    this.filter_grid.resetActiveCell();
  }

  TextFilter.prototype.handle_selection_changed = function(e, args){
    var all_rows = this.data_view.getItems();

    // Set selected to false for all visible rows (non visible rows
    // aren't included in the getSelectedRows, so we should leave the
    // state of those untouched)
    for (var row_index=0; row_index < all_rows.length; row_index++){
      var cur_row = all_rows[row_index];
      if (this.data_view.getRowById(cur_row.id) !== undefined){
        cur_row.selected = false;
      }
    }
    // Set selected to true for all selected rows
    var rows = this.row_selection_model.getSelectedRows();
    if (rows.length > 0){
      for (var row_index=0; row_index < rows.length; row_index++){
        var data_row_index = rows[row_index];
        var row = this.data_view.getItem(data_row_index);
        row.selected = true;
      }
    }
    // Regenerate the filter_sid_list by looping through all rows
    // (visible and filtered out) and adding them to the list if selected is true.
    this.filter_list = {};
    var something_selected = false
    for (var row_index=0; row_index < all_rows.length; row_index++){
      var row = all_rows[row_index];
      if (row.selected){
        something_selected = true;
        this.filter_list[row.value] = row.value;
      }
    }
    // If nothing is selected, then indicate that the grid should be unfiltered by setting
    // the filter_sid_list to null.
    if (!something_selected){
      this.filter_list = null;
    }

    // We want to resort the grid, but not immediately when a row is checked, because
    // it's jarring to have the row that the user just checked jump to the top of the grid.
    // Instead, we just set this flag so that we know to resort the grid the next time the filter
    // changes or the filter dropdown gets re-opened.
    this.sort_needed = true;

    $(this).trigger("filter_changed");
  }

  TextFilter.prototype.handle_filter_button_clicked = function(e){
    $.proxy(this.base.prototype.handle_filter_button_clicked.call(this, e), this);
    this.filter_grid.setColumns(this.filter_grid.getColumns());
    this.filter_grid.resizeCanvas();
    this.sort_if_needed();
    this.focus_on_search_box();
    return false;
  }

  TextFilter.prototype.is_active = function(){
    return this.filter_list != null;
  }

  TextFilter.prototype.reset_filter = function(){
    this.search_string = "";
    this.security_search.val("");
    this.data_view.refresh();
    this.row_selection_model.setSelectedRows([]);
    this.filter_list = null;
  }

  TextFilter.prototype.include_item = function(item){
    if (this.filter_list && !this.filter_list[item[this.field]]){
      return false;
    }
    return true;
  }

  return {'TextFilter': TextFilter}
});
