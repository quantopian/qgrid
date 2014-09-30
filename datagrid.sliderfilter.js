quanto.SliderFilter = class SliderFilter extends quanto.FilterBase
  constructor: ($context_elem, field, formatter) ->
    super($context_elem, field)
    @$slider_elem = @$filter_elem.find(".slider-range")
    @formatter = if formatter? then formatter else (value) => return value

  initialize_controls: (sid_info_list) =>
    super(sid_info_list)
    @$filter_elem.find(".min-value").html(@formatter(@min_value))
    @$filter_elem.find(".max-value").html(@formatter(@max_value))

    @slider_min = @min_value
    @slider_max = @max_value
    @$slider_elem.slider({
      range: true,
      min: @slider_min,
      max: @slider_max,
      values: [@slider_min, @slider_max],
      slide: (event, ui) =>
        @filter_value_min = ui.values[0]
        @filter_value_max = ui.values[1]
        @$filter_elem.find(".min-value").html(@formatter(@filter_value_min))
        @$filter_elem.find(".max-value").html(@formatter(@filter_value_max))

        if @filter_value_min == @slider_min
          @filter_value_min = null

        if @filter_value_max == @slider_max
          @filter_value_max = null

        $(@).trigger("filter_changed")
    })

    @handle_filtering_done()

  reset_filter: () =>
    @filter_value_min = null
    @filter_value_max = null

  is_active: () =>
    return @filter_value_min? || @filter_value_max?

  # This function gets called after update_min_max has been called for every row in the grid, which means
  # @updated_min_value and @updated_max_value are now up-to-date.
  handle_filtering_done: () =>
    min_val = @filter_value_min
    max_val = @filter_value_max

    # Only update the min/max for the slider if the user hasn't already adjusted their slider.  The reason is
    # because it would be weird for them to open up a slider that they had just moved and have it look totally
    # different than before.  The only way to update the min/max for a slider that was active when another filter
    # was changed is to reset the filter (either just this one, or all of them).
    if !@filter_value_min?
      min_val = @min_value
      if @updated_min_value?
        @slider_min = @updated_min_value
        min_val = @updated_min_value

    if !@filter_value_max?
      max_val = @max_value
      if @updated_max_value?
        @slider_max = @updated_max_value
        max_val = @updated_max_value

    @$slider_elem.slider({min: @slider_min, max: @slider_max}, values: [min_val, max_val])
    @$filter_elem.find(".min-value").html(@formatter(min_val))
    @$filter_elem.find(".max-value").html(@formatter(max_val))
    @update_filter_button_disabled()

  reset_min_max: () =>
    @updated_max_value = null
    @updated_min_value = null
    @first_value = null
    @has_multiple_values = false

  include_item: (item) =>
    include_item = true
    if @filter_value_min?
      if !item[@field]? || item[@field] < @filter_value_min
        include_item = false

    if @filter_value_max?
      if !item[@field]? || item[@field] > @filter_value_max
        include_item = false

    return include_item

  # Slider filters adjust their min/max when other filters cause rows to be excluded from the grid.  This is so the range
  # of values offered remains appropriate based on the rows in the grid.  This function gets called after all filters
  # have had an opportunity to decide whether they want to exclude a particular row (which they record in the "excluded_by"
  # hash).  This allows us to ignore rows that were excluded by filters other than this one in our calculation of the
  # min/max for this slider.
  update_min_max: (item) =>
    if !item.excluded_by? || (item.excluded_by[@field] || item.include)
      if !@updated_min_value? || item[@field] < @updated_min_value
        @updated_min_value = item[@field]
      if !@updated_max_value? || item[@field] > @updated_max_value
        @updated_max_value = item[@field]

      # In addition to adjusting the min/max, we also want to update the flag that tells us if there are multiple values
      # in this column.  If there's only one value, the filter button gets greyed out and we show a tooltip when it
      # gets clicked to explain that the filter would do nothing since there's only one value in the column.
      @update_has_multiple_values(item)

