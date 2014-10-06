define([
    'jquery',
    'handlebars',
    'filter_base',
    'jqueryui'
], function ($, handlebars, filter_base) {
  "use strict";

  var SliderFilter = function(field){
    this.base = filter_base.FilterBase;
    this.base(field);
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
    this.filter_elem.find(".min-value").html(this.min_value);
    this.filter_elem.find(".max-value").html(this.max_value);

    this.slider_min = this.min_value;
    this.slider_max = this.max_value;

    var step = (this.slider_max - this.slider_min) / 200;
    this.slider_elem.slider({
      range: true,
      min: this.slider_min,
      max: this.slider_max,
      values: [this.slider_min, this.slider_max],
      step: step,
      slide: $.proxy(function(event, ui){
        this.filter_value_min = ui.values[0];
        this.filter_value_max = ui.values[1];
        this.filter_elem.find(".min-value").html(this.filter_value_min);
        this.filter_elem.find(".max-value").html(this.filter_value_max);

        if (this.filter_value_min == this.slider_min){
          this.filter_value_min = null;
        }

        if (this.filter_value_max == this.slider_max){
          this.filter_value_max = null;
        }

        $(this).trigger("filter_changed");
      }, this)
    });

    this.handle_filtering_done();
  }

  SliderFilter.prototype.reset_filter = function(){
    this.filter_value_min = null;
    this.filter_value_max = null;
  }

  SliderFilter.prototype.is_active = function(){
    return this.filter_value_min || this.filter_value_max;
  }

  // This function gets called after update_min_max has been called for every row in the grid, which means
  // this.updated_min_value and this.updated_max_value are now up-to-date.
  SliderFilter.prototype.handle_filtering_done = function(){
    var min_val = this.filter_value_min;
    var max_val = this.filter_value_max;

    // Only update the min/max for the slider if the user hasn't already adjusted their slider.  The reason is
    // because it would be weird for them to open up a slider that they had just moved and have it look totally
    // different than before.  The only way to update the min/max for a slider that was active when another filter
    // was changed is to reset the filter (either just this one, or all of them).
    if (!this.filter_value_min){
      min_val = this.min_value;
      if (this.updated_min_value){
        this.slider_min = this.updated_min_value;
        min_val = this.updated_min_value;
      }
    }

    if (!this.filter_value_max){
      max_val = this.max_value;
      if (this.updated_max_value){
        this.slider_max = this.updated_max_value;
        max_val = this.updated_max_value;
      }
    }

    if (this.slider_elem){
      var step = (this.slider_max - this.slider_min) / 200;
      this.slider_elem.slider({min: this.slider_min, max: this.slider_max, values: [min_val, max_val], step: step});
      this.filter_elem.find(".min-value").html(min_val);
      this.filter_elem.find(".max-value").html(max_val);
    }
    this.update_filter_button_disabled();
  }

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
  }

  // Slider filters adjust their min/max when other filters cause rows to be excluded from the grid.  This is so the range
  // of values offered remains appropriate based on the rows in the grid.  This function gets called after all filters
  // have had an opportunity to decide whether they want to exclude a particular row (which they record in the "excluded_by"
  // hash).  This allows us to ignore rows that were excluded by filters other than this one in our calculation of the
  // min/max for this slider.
  SliderFilter.prototype.update_min_max = function(item){
    if (!item.excluded_by || (item.excluded_by[this.field] || item.include)){
      if (!this.updated_min_value || item[this.field] < this.updated_min_value){
        this.updated_min_value = item[this.field];
      }
      if (!this.updated_max_value || item[this.field] > this.updated_max_value){
        this.updated_max_value = item[this.field];
      }
    }

      // In addition to adjusting the min/max, we also want to update the flag that tells us if there are multiple values
      // in this column.  If there's only one value, the filter button gets greyed out and we show a tooltip when it
      // gets clicked to explain that the filter would do nothing since there's only one value in the column.
      this.update_has_multiple_values(item);
  }

  return {'SliderFilter': SliderFilter}
});
