define([
    'jquery',
    'handlebars',
], function ($, handlebars) {
  "use strict";

  var FilterBase = function(field, column_type, precision){
    this.field = field;
    this.column_type = column_type;
    this.precision = precision;
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

  FilterBase.prototype.create_error_msg = function(){
    var error_template =  handlebars.compile(
      "<div class='filter-error-msg dropdown-menu {{type}}-filter'>" +
        "All values in the column are the same.  Nothing to filter." +
      "</div>"
    );
    this.filter_elem = $(error_template(this.column));
    this.initialize_controls();
    this.disabled_tooltip_showing = true;
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
    $(this).trigger("get_column_min_max", this.field);
    return false;
  }

  FilterBase.prototype.update_min_max = function(column_info){
    throw new Error("not implemented!");
  }

  FilterBase.prototype.show_filter = function(){
    this.column_header_elem.addClass("active");

    this.prev_column_separator = this.column_header_elem.prev(".slick-header-column").find(".slick-resizable-handle");
    this.prev_column_separator.addClass("active");

    this.filter_btn.addClass("active");

    if (this.has_multiple_values || this.is_active()){
      if (!this.filter_elem) {
        this.create_filter_elem();
      }
    } else {
      this.create_error_msg();
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

  FilterBase.prototype.hide_filter = function(){
    if (!this.filter_elem)
        return;
    if (this.disabled_tooltip_showing){
      this.filter_elem.hide();
      this.filter_elem = null;
      this.disabled_tooltip_showing = false;
    } else if (!this.filter_elem.hasClass("hidden")){
      this.filter_elem.hide();
      this.filter_elem.appendTo($(".filter-dropdowns"));
    }
    this.filter_btn.removeClass("active");
    this.column_header_elem.removeClass("active");
    this.prev_column_separator.removeClass("active");
  }

  FilterBase.prototype.handle_body_key_up = function(e){
    if (e.keyCode == 27){ // esc key
      this.hide_filter();
    }
  }

  FilterBase.prototype.handle_body_mouse_down = function (e){
    if (this.filter_elem && this.filter_elem[0] != e.target &&
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
    $(this).trigger("filter_changed", this.get_filter_info());
    // The "false" parameter tells backtest_table_manager that we want to recalculate the min/max values for this filter
    // based on the rows that are still included in the grid.  This is because if this filter was already active,
    // its min/max could be out-of-date because we don't adjust the min/max on active filters (to prevent confusion).
    // This is currently the only filter_changed case where it's appropriate to have this filter's min/max recalculated,
    // because you wouldn't want to adjust a slider's min/max while the user was moving the slider, for example.
    return false;
  };

  FilterBase.prototype.reset_filter = function(){
    throw new Error("not implemented!");
  };

  FilterBase.prototype.get_filter_info = function(){
    throw new Error("not implemented!");
  };

//
//  filter_done: () =>
//    throw new Error("not implemented!")
//
  FilterBase.prototype.include_item = function(item){
    throw new Error("not implemented!");
  }

  return {'FilterBase': FilterBase};
});
