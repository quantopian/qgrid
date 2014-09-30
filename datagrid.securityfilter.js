quanto.SecurityFilter = class SecurityFilter extends quanto.FilterBase
  constructor: ($context_elem, field) ->
    super($context_elem, field)
    @append_cash_row = false

  initialize_controls: (sid_info_list) =>
    super(sid_info_list)
    @sid_infos = _.values(sid_info_list)
    @search_string = ""

    if @append_cash_row
      @sid_infos.push({name: "Cash", ticker: "Cash", sid: "Cash"})

    # slick grid requires and id field on each object
    for cur_sid in @sid_infos
      cur_sid.id = cur_sid.sid

    @data_view = new Slick.Data.DataView({
      inlineFilters: false,
      enableTextSelectionOnCells: true
    })

    security_filter = (item, args) =>
      if @search_string?
        if item.ticker.toLowerCase().indexOf(@search_string.toLowerCase()) == -1 &&
        item.name.toLowerCase().indexOf(@search_string.toLowerCase()) == -1 &&
        item.sid.indexOf(@search_string) == -1
          return false
      return true

    @data_view.beginUpdate()
    @data_view.setItems(@sid_infos)
    @data_view.setFilter(security_filter)
    @data_view.sort(@sort_comparer, true)
    @data_view.endUpdate()

    name_formatter = (row, cell, value, columnDef, dataContext) =>
      if dataContext.sid == "Cash"
        return "<span class='label label-cash'>Cash</span>"
      else
        return "<span class='security-name'>#{_.str.titleize(dataContext.name.toLowerCase())}</span>
                      <small class='security-ticker'>#{dataContext.ticker.toLowerCase()} (#{dataContext.sid})</small>"

    checkboxSelector = new Slick.CheckboxSelectColumn({
      cssClass: "check-box-cell"
    })

    columns = [
      checkboxSelector.getColumnDefinition(),
      {
        id: "name",
        name: "Name",
        field: "name",
        formatter: name_formatter,
        sortable: true
        width: 400,
      }]

    options =
      enableCellNavigation: true,
      fullWidthRows: true,
      syncColumnCellResize: true,
      rowHeight: 32,
      forceFitColumns: false,
      enableColumnReorder: false

    @security_grid = new Slick.Grid(@$filter_elem.find(".text-filter-grid"), @data_view,  columns, options)
    @security_grid.registerPlugin(checkboxSelector)
    @security_grid.registerPlugin(new Slick.AutoTooltips())

    @row_selection_model = new Slick.RowSelectionModel({selectActiveRow: false})
    @row_selection_model.onSelectedRangesChanged.subscribe(@handle_selection_changed)

    @security_grid.setSelectionModel(@row_selection_model);
    @data_view.syncGridSelection(@security_grid, true, true)
    @security_grid.render()

    @data_view.onRowCountChanged.subscribe((e, args) =>
      @security_grid.updateRowCount()
      @security_grid.render()
    )

    @data_view.onRowsChanged.subscribe((e, args) =>
      @security_grid.invalidateRows(args.rows)
      @security_grid.render()
    )

    @$security_search = @$filter_elem.find(".search-input")
    @$security_search.keyup(@handle_text_input_key_up)
    @$security_search.click(@handle_text_input_click)

    @security_grid.onClick.subscribe(@handle_grid_clicked)
    @security_grid.onKeyDown.subscribe(@handle_grid_key_down)

    @$filter_elem.find("a.select-all-link").click((e) =>
      @reset_filter()
      all_row_indices = []
      all_rows = @data_view.getItems()
      for row, i in all_rows
        all_row_indices.push(i)
      @row_selection_model.setSelectedRows(all_row_indices)
      $(@).trigger("filter_changed")
      return false
    )

  handle_text_input_click: (e) =>
    @security_grid.resetActiveCell()

  handle_text_input_key_up: (e) =>
    old_search_string = @search_string
    if e.keyCode == 40 # down arrow
      @security_grid.focus()
      @security_grid.setActiveCell(0, 0)
      return
    if e.keyCode == 13 # enter key
      if @security_grid.getDataLength() > 0
        @toggle_row_selected(0)
        @$security_search.val("")
    @search_string = @$security_search.val()
    if old_search_string != @search_string
      @data_view.refresh()
      @sort_if_needed()

  toggle_row_selected: (row_index) =>
    old_selected_rows = @row_selection_model.getSelectedRows()
    # if the row is already selected, remove it from the selected rows array.
    selected_rows = old_selected_rows.filter (word) -> word isnt row_index
    # otherwise add it to the selected rows array so it gets selected
    if selected_rows.length == old_selected_rows.length
      selected_rows.push(row_index)
    @row_selection_model.setSelectedRows(selected_rows)

  handle_grid_clicked: (e, args) =>
    @toggle_row_selected(args.row)
    active_cell = @security_grid.getActiveCell()
    if !active_cell?
      e.stopImmediatePropagation()

  handle_grid_key_down: (e, args) =>
    active_cell = @security_grid.getActiveCell()
    if active_cell?
      if e.keyCode == 13 # enter key
        @toggle_row_selected(active_cell.row)
        return

      # focus on the search box for any key other than the up/down arrows
      if e.keyCode != 40 && e.keyCode != 38
        @focus_on_search_box()
        return

        # also focus on the search box if we're at the top of the grid and this is the up arrow
      else if active_cell.row == 0 && e.keyCode == 38
        @focus_on_search_box()
        e.preventDefault()
        return

  handle_selection_changed: (e, args) =>
    all_rows = @data_view.getItems()

    # Set selected to false for all visible rows (non visible rows
    # aren't included in the getSelectedRows, so we should leave the
    # state of those untouched)
    for row in all_rows
      if @data_view.getRowById(row.id)?
        row.selected = false

    # Set selected to true for all selected rows
    rows = @row_selection_model.getSelectedRows()
    if rows.length > 0
      for row_index in rows
        row = @data_view.getItem(row_index)
        row.selected = true

    # Regenerate the filter_sid_list by looping through all rows
    # (visible and filtered out) and adding them to the list if selected is true.
    @filter_sid_list = {}
    something_selected = false
    for row in all_rows
      if row.selected
        something_selected = true
        @filter_sid_list[row.id] = row.id

    # If nothing is selected, then indicate that the grid should be unfiltered by setting
    # the filter_sid_list to null.
    if !something_selected
      @filter_sid_list = null

    # We want to resort the grid, but not immediately when a row is checked, because
    # it's jarring to have the row that the user just checked jump to the top of the grid.
    # Instead, we just set this flag so that we know to resort the grid the next time the filter
    # changes or the filter dropdown gets re-opened.
    @sort_needed = true

    $(@).trigger("filter_changed")

  sort_if_needed: (force = false) =>
    if force || @sort_needed
      @data_view.sort(@sort_comparer, true)
      @sort_needed = false

  focus_on_search_box: () =>
    @$security_search.focus().val(@search_string)
    @security_grid.resetActiveCell()

  handle_filter_button_clicked: (e) =>
    super(e)
    @security_grid.setColumns(@security_grid.getColumns())
    @security_grid.resizeCanvas()
    @sort_if_needed()
    @focus_on_search_box()
    return false

  sort_comparer: (x, y) =>
    x_value = x.name
    y_value = y.name

    # selected row should be sorted to the top
    if x.selected != y.selected
      if x.selected then return -1 else return 1

    if x.sid == "Cash" then return 1
    if y.sid == "Cash" then return -1

    return if x_value > y_value then 1 else -1

  is_active: () =>
    return @filter_sid_list?

  reset_filter: () =>
    @search_string = ""
    @$security_search.val("")
    @data_view.refresh()
    @row_selection_model.setSelectedRows([])
    @sort_if_needed(true)
    @filter_sid_list = null

  include_item: (item) =>
    if @filter_sid_list?
      if !@filter_sid_list[item.sid]?
        return false
    return true
