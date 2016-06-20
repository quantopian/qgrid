define([
    'jquery'
], function ($) {
  "use strict";

  var FilterBase = function(field){
    this.field = field;
    this.has_multiple_values = true;
  }

  FilterBase.prototype.render_filter_button = function(column_header_elem, slick_grid){
    if (this.filter_btn)
      this.filter_btn.off();

    this.column_header_elem = column_header_elem;
    this.slick_grid = slick_grid;
    this.filter_btn = $("<div class='fa fa-filter icon-filter filter-button'>");
    this.filter_btn.appendTo(this.column_header_elem);
    this.filter_btn.click($.proxy(this.handle_filter_button_clicked, this));
    this.update_filter_button_disabled();
  }

  FilterBase.prototype.create_filter_elem = function(){
    this.filter_template = this.get_filter_template();
    this.filter_elem = $(this.filter_template(this.column));
    this.initialize_controls();
    return this.filter_elem;
  }

  FilterBase.prototype.get_filter_template = function(item){
    throw new Error("not implemented!");
  }

  // If all the values in this column are the same, the filters would accomplish nothing,
  // so we gray out the filter button.  If the button is clicked we show a tooltip explaining
  // why the filter is disabled.
  FilterBase.prototype.update_filter_button_disabled = function(){
    if (this.column_header_elem){
      if (this.has_multiple_values || this.is_active()){
        this.column_header_elem.removeClass("filter-button-disabled");
      }else {
        this.column_header_elem.addClass("filter-button-disabled");
      }
    }
  }

  FilterBase.prototype.is_active = function(){
    return false;
  }

  FilterBase.prototype.handle_filter_button_clicked = function(e){
    this.column = this.column_header_elem.data("column");

    if (this.has_multiple_values || this.is_active()){
      this.column_header_elem.addClass("active");

      this.prev_column_separator = this.column_header_elem.prev(".slick-header-column").find(".slick-resizable-handle");
      this.prev_column_separator.addClass("active");

      this.filter_btn.addClass("active");

      if (!this.filter_elem){
        this.filter_elem = this.create_filter_elem();
      }

      this.filter_elem.appendTo(this.column_header_elem.closest(".q-grid-container")).show();

      // position the dropdown
      var top = this.filter_btn.offset().top + this.filter_btn.height();
      var left = this.filter_btn.offset().left;

      var filter_width = this.filter_elem.width();
      var elem_right = left + filter_width;

      var qgrid_area = this.filter_elem.closest('.q-grid-container');
      if (elem_right > qgrid_area.offset().left + qgrid_area.width()){
        left = (this.filter_btn.offset().left + this.filter_btn.width()) - filter_width;
      }

      this.filter_elem.offset({ top: 0, left: 0 });
      this.filter_elem.offset({ top: top, left: left });
    }
    else{
      this.filter_btn.tooltip({
        placement: "bottom",
        title: "This filter is disabled because all of the values in this column are the same.",
        trigger: "manual"
//        container: "#" + this.context_elem.attr("id")
      });
      this.filter_btn.tooltip("show");
      this.disabled_tooltip_showing = true;
    }
    return false;
  }

  FilterBase.prototype.hide_filter = function(){
    if (!this.filter_elem.hasClass("hidden")){
      this.filter_elem.hide();
      this.filter_elem.appendTo($(".filter-dropdowns"));
      this.filter_btn.removeClass("active");
      this.column_header_elem.removeClass("active");
      this.prev_column_separator.removeClass("active");
    }
    else if (this.disabled_tooltip_showing){
      this.filter_btn.tooltip("destroy");
      this.disabled_tooltip_showing = false;
    }
  }

  FilterBase.prototype.handle_body_key_up = function(e){
    if (e.keyCode == 27){ // esc key
      this.hide_filter();
    }
  }

  FilterBase.prototype.handle_body_mouse_down = function (e){
    if (this.filter_elem[0] != e.target &&
      !$.contains(this.filter_elem[0], e.target) &&
      $(e.target).closest(".filter-child-elem").length == 0){
        this.hide_filter();
    }
    return true;
  }

  FilterBase.prototype.initialize_controls = function(){
    this.filter_elem.find("a.reset-link").click($.proxy(this.handle_reset_filter_clicked, this));

    var self = this;
    this.filter_elem.find("i.close-button").click(function(e){
      self.hide_filter();
      return false;
    });

    $(document.body).bind("mousedown", $.proxy(this.handle_body_mouse_down, this));
    $(document.body).bind("keyup", $.proxy(this.handle_body_key_up, this));
  }

  FilterBase.prototype.handle_reset_filter_clicked = function(e){
    this.reset_filter();
    // The "false" parameter tells backtest_table_manager that we want to recalculate the min/max values for this filter
    // based on the rows that are still included in the grid.  This is because if this filter was already active,
    // its min/max could be out-of-date because we don't adjust the min/max on active filters (to prevent confusion).
    // This is currently the only filter_changed case where it's appropriate to have this filter's min/max recalculated,
    // because you wouldn't want to adjust a slider's min/max while the user was moving the slider, for example.
    $(this).trigger("filter_changed", false);
    return false
  }
//
//  reset_filter: () =>
//    throw new Error("not implemented!")
//
//  filter_done: () =>
//    throw new Error("not implemented!")
//
  FilterBase.prototype.include_item = function(item){
    throw new Error("not implemented!");
  }

  FilterBase.prototype.update_has_multiple_values = function(item){
    // Record the first value, and then set the this.has_multiple_values flag to true as soon as we receive a row that has
    // a different value from that first value.  We need this info because if this column has all the same
    // values we don't show the filter button at all (since the filter would be useless).
    if (!this.first_value){
      this.first_value = item[this.field];
    }
    if (!this.has_multiple_values && this.first_value != item[this.field]){
      this.has_multiple_values = true;
    }
  }

  FilterBase.prototype.handle_row_data = function(item){
    this.update_has_multiple_values(item);
    this.initialize_min_max(item);
  }

  FilterBase.prototype.initialize_min_max = function(item){
    if (!this.max_value || item[this.field] > this.max_value){
      this.max_value = item[this.field];
    }

    if (!this.min_value || item[this.field] < this.min_value){
      this.min_value = item[this.field];
    }
  }

  return {'FilterBase': FilterBase};
});
