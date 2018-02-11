var filter_base = require('./qgrid.filterbase.js');

class SliderFilter extends filter_base.FilterBase {

  get_filter_html() {
    return `
      <div class='numerical-filter grid-filter qgrid-dropdown-menu'>
        <h3 class='qgrid-popover-title'>
          <div class='dropdown-title'>Filter by ${this.field}</div>
          <i class='fa fa-times icon-remove close-button'/>
        </h3>
        <div class='dropdown-body'>
          <div class='slider-range'/>
          <span class='slider-label'>
            <span class='min-value'>0</span>
            <span class='range-separator'>-</span>
            <span class='max-value'>100</span>
          </span>
        </div>
        <div class='dropdown-footer'>
          <a class='reset-link' href='#'>Reset</a>
        </div>
      </div>
    `;
  }

  initialize_controls() {
    super.initialize_controls();
    this.slider_elem = this.filter_elem.find(".slider-range");

    var values_to_set = [
      this.filter_value_min || this.min_value,
      this.filter_value_max || this.max_value
    ];

    this.set_value(values_to_set[0], values_to_set[1]);

    this.slider_elem.slider({
      range: true,
      min: this.min_value,
      max: this.max_value,
      values: values_to_set,
      step: this.get_slider_step(),
      slide: (event, ui) => {
        if (this.slide_timeout) {
          clearTimeout(this.slide_timeout);
        }
        this.slide_timeout = setTimeout(() => {
          var slider_values = this.slider_elem.slider("option", "values");
          this.filter_value_min = slider_values[0];
          this.filter_value_max = slider_values[1];
          this.set_value(this.filter_value_min, this.filter_value_max);

          if (this.filter_value_min == this.min_value) {
            this.filter_value_min = null;
          }

          if (this.filter_value_max == this.max_value) {
            this.filter_value_max = null;
          }

          this.send_filter_changed();
          this.slide_timeout = null;
        }, 100);
      }
    });
  }

  set_value(min_val, max_val) {
    var min_val_rounded, max_val_rounded;
    if (this.column_type == 'integer') {
      min_val_rounded = min_val.toFixed(0);
      max_val_rounded = max_val.toFixed(0);
    } else {
      min_val_rounded = min_val.toFixed(this.precision);
      max_val_rounded = max_val.toFixed(this.precision);
    }
    this.filter_elem.find(".min-value").html(min_val_rounded);
    this.filter_elem.find(".max-value").html(max_val_rounded);
  }

  get_slider_step() {
    if (this.column_type == "integer") {
      return 1;
    } else {
      return (this.max_value - this.min_value) / 200;
    }
  }

  reset_filter() {
    this.filter_value_min = null;
    this.filter_value_max = null;
    if (this.slider_elem) {
      var step = this.get_slider_step();
      this.slider_elem.slider({
        min: this.min_value,
        max: this.max_value,
        values: [this.min_value, this.max_value],
        step: step
      });
      this.set_value(this.min_value, this.max_value);
    }
    this.send_filter_changed();
  }

  is_active() {
    return this.filter_value_min != null || this.filter_value_max != null;
  }

  update_min_max(col_info, has_active_filter) {
    this.min_value = col_info.slider_min;
    this.max_value = col_info.slider_max;

    var filter_info = col_info.filter_info;
    if (filter_info) {
      this.filter_value_min = filter_info.min || this.min_value;
      this.filter_value_max = filter_info.max || this.max_value;
    } else {
      this.filter_value_min = null;
      this.filter_value_max = null;
    }
    this.has_multiple_values = this.min_value != this.max_value;

    this.show_filter();

    if (!has_active_filter) {
      this.update_filter_button_disabled();
    }
  }

  get_filter_info() {
    return {
      "field": this.field,
      "type": "slider",
      "min": this.filter_value_min,
      "max": this.filter_value_max
    };
  }
}

module.exports = {'SliderFilter': SliderFilter};
