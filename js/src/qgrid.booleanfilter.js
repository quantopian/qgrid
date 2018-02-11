var $ = require('jquery');
var filter_base = require('./qgrid.filterbase.js');

class BooleanFilter extends filter_base.FilterBase {

  get_filter_html() {
    return `
      <div class='boolean-filter grid-filter qgrid-dropdown-menu'>
        <h3 class='qgrid-popover-title'>
          <div class='dropdown-title'>Filter by ${this.field}</div>
          <i class='fa fa-times icon-remove close-button'/>
        </h3>
        <div class='dropdown-body'>
          <form>
            <div class="bool-radio-wrapper">
              <label class="radio-label label-true" for="radio-true">True</label>
              <input type="radio" name="bool-filter-radio"
                class="bool-filter-radio" id="radio-true" value="true">
              <label class="radio-label label-false" for="radio-false">False</label>
              <input type="radio" name="bool-filter-radio"
                class="bool-filter-radio" id="radio-false" value="false">
            </div>
          </form>
          <div class='no-results hidden'>No results found.</div>
        </div>
        <div class='dropdown-footer'>
          <a class='reset-link' href='#'>Reset</a>
        </div>
      </div>
    `;
  }

  update_min_max(col_info, has_active_filter) {
    this.values = col_info.values;
    this.length = col_info.length;
    if('filter_info' in col_info){
      this.selected = col_info.filter_info.selected;
    } else {
      this.selected = null;
    }
    this.show_filter();
  }

  initialize_controls() {
    super.initialize_controls();
    this.radio_buttons = this.filter_elem.find('.bool-filter-radio');

    this.filter_elem.find('label').click((e) => {
      var radio_id = $(e.currentTarget).attr('for');
      this.radio_buttons.filter(`#${radio_id}`).click();
    });

    if (this.selected == null) {
      this.radio_buttons.prop('checked', false);
    } else {
      this.radio_buttons.filter(
          `#radio-${this.selected}`
      ).prop('checked', true);
    }

    this.radio_buttons.change(() => {
      var checked_radio = this.radio_buttons.filter(':checked');
      var old_selected_value = this.selected;
      if (checked_radio.length == 0) {
        this.selected = null;
      } else {
        this.selected = checked_radio.val() == 'true';
      }
      if (this.selected != old_selected_value) {
        this.send_filter_changed();
      }
    });
  }

  is_active() {
    return this.selected != null;
  }

  reset_filter() {
    this.radio_buttons.prop('checked', false);
    this.selected = null;
    this.send_filter_changed();
  }

  get_filter_info() {
    return {
      "field": this.field,
      "type": "boolean",
      "selected": this.selected
    };
  }
}

module.exports = {'BooleanFilter': BooleanFilter};
