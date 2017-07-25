define([
    'jquery',
    'handlebars',
    './qgrid.filterbase.js',
    'jquery-ui'
], function ($, handlebars, filter_base) {
  "use strict";

  var SliderFilter = function(field, column_type, precision){
    this.base = filter_base.FilterBase;
    this.base(field, column_type, precision);
  }
  SliderFilter.prototype = new filter_base.FilterBase;

  SliderFilter.prototype.get_filter_template = function(){
    return handlebars.compile(
      "<div class='numerical-filter grid-filter dropdown-menu {{type}}-filter'>" +
        "<h3 class='popover-title'>" +
          "<div class='dropdown-title'>Filter by {{name}}</div>" +
          "<i class='fa fa-times icon-remove close-button'/>" +
        "</h3>" +
        "<div class='dropdown-body'>" +
          "<div class='slider-range'/>" +
          "<span class='slider-label'>" +
            "<span class='min-value'>0</span>" +
            "<span class='range-separator'>-</span>" +
            "<span class='max-value'>100</span>" +
          "</span>" +
        "</div>" +
        "<div class='dropdown-footer'>" +
          "<a class='reset-link' href='#'>Reset</a>"+
        "</div>" +
      "</div>"
    );
  }

  SliderFilter.prototype.include_item = function(item){
    var include_item = true;
    if (this.filter_value_min){
      if (!item[this.field] || item[this.field] < this.filter_value_min){
        include_item = false;
      }
    }

    if (this.filter_value_max){
      if (!item[this.field] || item[this.field] > this.filter_value_max){
        include_item = false;
      }
    }

    return include_item;
  }

  SliderFilter.prototype.initialize_controls = function(){
    $.proxy(this.base.prototype.initialize_controls.call(this), this);
    this.slider_elem = this.filter_elem.find(".slider-range");
    this.set_value(this.min_value, this.max_value);

    this.slider_min = this.min_value;
    this.slider_max = this.max_value;

    this.slider_elem.slider({
      range: true,
      min: this.slider_min,
      max: this.slider_max,
      values: [this.filter_value_min, this.filter_value_max],
      step: this.get_slider_step(),
      slide: $.proxy(function(event, ui){
        if (this.slide_timeout){
          clearTimeout(this.slide_timeout);
        }
        this.slide_timeout = setTimeout($.proxy(function(){
          this.filter_value_min = ui.values[0];
          this.filter_value_max = ui.values[1];
          this.set_value(this.filter_value_min, this.filter_value_max);

          if (this.filter_value_min == this.slider_min){
            this.filter_value_min = null;
          }

          if (this.filter_value_max == this.slider_max){
            this.filter_value_max = null;
          }

          $(this).trigger("filter_changed", this.get_filter_info());
          this.slide_timeout = null;
        }, this), 100);
      }, this)
    });
  }

  SliderFilter.prototype.set_value = function(min_val, max_val){
    if (this.column_type == 'integer'){
        var min_val_rounded = min_val.toFixed(0);
        var max_val_rounded = max_val.toFixed(0);
      } else {
        var min_val_rounded = min_val.toPrecision(this.precision);
        var max_val_rounded = max_val.toPrecision(this.precision);
      }
      this.filter_elem.find(".min-value").html(min_val_rounded);
      this.filter_elem.find(".max-value").html(max_val_rounded);
  }

  SliderFilter.prototype.get_slider_step = function(){
    if (this.column_type == "integer"){
      return 1;
    } else {
      return (this.max_value - this.min_value) / 200;
    }
  }

  SliderFilter.prototype.reset_filter = function(){
    this.filter_value_min = null;
    this.filter_value_max = null;
    if (this.slider_elem){
      var step = this.get_slider_step();
      this.slider_elem.slider({min: this.min_value, max: this.max_value, values: [this.min_value, this.max_value], step: step});
      this.set_value(this.min_value, this.max_value)
    }
    this.update_filter_button_disabled();
  }

  SliderFilter.prototype.is_active = function(){
    return this.filter_value_min || this.filter_value_max;
  }

  SliderFilter.prototype.update_min_max = function(col_info){
    this.min_value = col_info['slider_min'];
    this.max_value = col_info['slider_max'];

    var filter_info = col_info['filter_info'];
    if (filter_info){
      this.filter_value_min = filter_info['min'] || this.min_value;
      this.filter_value_max = filter_info['max'] || this.max_value;
    } else {
      this.filter_value_min = this.min_value;
      this.filter_value_max = this.max_value;
    }

    this.has_multiple_values = this.min_value != this.max_value;
    $.proxy(this.base.prototype.show_filter.call(this), this);
  };

  SliderFilter.prototype.reset_min_max = function(){
    this.updated_max_value = null;
    this.updated_min_value = null;
    this.first_value = null;
    this.has_multiple_values = false;
  }

  SliderFilter.prototype.include_item = function(item){
    var include_item = true;
    if (this.filter_value_min){
      if (!item[this.field] || item[this.field] < this.filter_value_min){
        include_item = false;
      }
    }
    if (this.filter_value_max){
      if (!item[this.field] || item[this.field] > this.filter_value_max){
        include_item = false;
      }
    }

    return include_item;
  };

  SliderFilter.prototype.get_filter_info = function(){
      return {
        "field": this.field,
        "type": "slider",
        "min": this.filter_value_min,
        "max": this.filter_value_max
      }
  };

  return {'SliderFilter': SliderFilter}
});
