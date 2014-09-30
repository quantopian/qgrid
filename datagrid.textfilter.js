quanto.TextFilter = class TextFilter extends quanto.FilterBase
  constructor: ($context_elem, field) ->
    super($context_elem, field)
    @items_hash = {}

  initialize_min_max: (item) =>
    super(item)
    item_value = item[@field]
    @items_hash[item_value] = {id: item_value, value: item_value}

  initialize_controls: (sid_info_list) =>
    super(sid_info_list)
    @grid_items = _.values(@items_hash)

    @data_view = new Slick.Data.DataView({
      inlineFilters: false,
      enableTextSelectionOnCells: true
    })

    sort_comparer = (x, y) =>
      x_value = x.value
      y_value = y.value
      return if x_value > y_value then 1 else -1

    @data_view.beginUpdate()
    @data_view.setItems(@grid_items)
    @data_view.sort(sort_comparer, true)
    @data_view.endUpdate()

    row_formatter = (row, cell, value, columnDef, dataContext) =>
      return "<span class='text-filter-value'>#{dataContext.value}</span>"

    checkboxSelector = new Slick.CheckboxSelectColumn({
      cssClass: "check-box-cell"
    })

    columns = [
      checkboxSelector.getColumnDefinition(),
      {
        id: "name",
        name: "Name",
        field: "name",
        formatter: row_formatter,
        sortable: true
      }]

    options =
      enableCellNavigation: true,
      fullWidthRows: true,
      syncColumnCellResize: true,
      rowHeight: 32,
      forceFitColumns: true,
      enableColumnReorder: false,
      autoHeight: true

    @filter_grid = new Slick.Grid(@$filter_elem.find(".text-filter-grid"), @data_view,  columns, options)
    @filter_grid.registerPlugin(checkboxSelector)

    @row_selection_model = new Slick.RowSelectionModel({selectActiveRow: false})
    @row_selection_model.onSelectedRangesChanged.subscribe(@handle_selection_changed)

    @filter_grid.setSelectionModel(@row_selection_model);
    @data_view.syncGridSelection(@filter_grid, true, true)
    @filter_grid.render()

    @data_view.onRowCountChanged.subscribe((e, args) =>
      @filter_grid.updateRowCount()
      @filter_grid.render()
    )

    @data_view.onRowsChanged.subscribe((e, args) =>
      @filter_grid.invalidateRows(args.rows)
      @filter_grid.render()
    )

    @filter_grid.onClick.subscribe(@handle_grid_clicked)
    @filter_grid.onKeyDown.subscribe(@handle_grid_key_down)

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
    active_cell = @filter_grid.getActiveCell()
    if !active_cell?
      e.stopImmediatePropagation()

  handle_selection_changed: (e, args) =>
    rows = @row_selection_model.getSelectedRows()
    @filter_list = {}
    if rows.length > 0
      for row_index in rows
        row = @data_view.getItem(row_index)
        @filter_list[row.value] = row.value
    else
      @filter_list = null

    $(@).trigger("filter_changed")

  handle_filter_button_clicked: (e) =>
    super(e)
    @filter_grid.setColumns(@filter_grid.getColumns())
    @filter_grid.resizeCanvas()
    return false

  is_active: () =>
    return @filter_list?

  reset_filter: () =>
    @row_selection_model.setSelectedRows([])
    @filter_list = null

  include_item: (item) =>
    if @filter_list?
      if !@filter_list[item[@field]]?
        return false
    return true
