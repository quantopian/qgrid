var $ = require('jquery');

class FilterBase {
  constructor(field, column_type, qgrid) {
    this.field = field;
    this.column_type = column_type;
    this.qgrid = qgrid;
    this.widget_model = qgrid.model;
    if (this.widget_model) {
      this.precision = this.widget_model.get('precision');
    }
    this.has_multiple_values = true;
  }

  handle_msg(msg) {
    var column_info = msg.col_info;
    if (msg.type == 'column_min_max_updated'){
      this.update_min_max(column_info, this.qgrid.has_active_filter());
    }
  }

  update_min_max(column_info, has_active_filter) {
    throw new Error("not implemented!");
  }

  render_filter_button(column_header_elem, slick_grid) {
    if (this.filter_btn)
      this.filter_btn.off();

    this.column_header_elem = column_header_elem;
    this.slick_grid = slick_grid;
    this.filter_btn = $(`
      <div class='filter-button'>
        <div class='fa fa-filter filter-icon'/>
      </div>
    `);
    this.filter_icon = this.filter_btn.find('.filter-icon');
    this.filter_btn.appendTo(this.column_header_elem);
    this.filter_btn.click((e) => this.handle_filter_button_clicked(e));
  }

  create_filter_elem() {
    this.filter_elem = $(this.get_filter_html());
    this.initialize_controls();
    return this.filter_elem;
  }

  create_error_msg() {
    var error_html = `
      <div class='filter-error-msg grid-filter'>
        All values in the column are the same.  Nothing to filter.
      </div>
    `;
    this.filter_elem = $(error_html);
    this.initialize_controls();
    this.disabled_tooltip_showing = true;
  }

  get_filter_html() {
    throw new Error("not implemented!");
  }

  // If all the values in this column are the same, the filters would accomplish nothing,
  // so we gray out the filter button.  If the button is clicked we show a tooltip explaining
  // why the filter is disabled.
  update_filter_button_disabled() {
    if (this.column_header_elem) {
      if (this.has_multiple_values || this.is_active()) {
        this.column_header_elem.removeClass("filter-button-disabled");
      } else {
        this.column_header_elem.addClass("filter-button-disabled");
      }
    }
  }

  is_active() {
    throw new Error("not implemented!");
  }

  handle_filter_button_clicked(e) {
    if (this.filter_btn.hasClass('active')){
      this.hide_filter();
      e.stopPropagation();
      return false;
    }

    this.filter_icon.removeClass('fa-filter');
    this.filter_icon.addClass('fa-spinner fa-spin');
    this.filter_btn.addClass('disabled');

    var msg = {
        'type': 'show_filter_dropdown',
        'field': this.field,
        'search_val': null
    };
    this.widget_model.send(msg);
    return false;
  }

  show_filter() {
    this.column_header_elem.addClass("active");

    this.prev_column_separator = this.column_header_elem.prev(".slick-header-column").find(".slick-resizable-handle");
    this.prev_column_separator.addClass("active");

    this.filter_btn.removeClass('disabled');
    this.filter_btn.addClass("active");

    this.filter_icon.removeClass('fa-spinner fa-spin');
    this.filter_icon.addClass('fa-filter');

    if (this.has_multiple_values || this.is_active()) {
      this.create_filter_elem();
    } else {
      this.create_error_msg();
    }

    this.filter_elem.appendTo(this.column_header_elem.closest(".q-grid-container")).show();

    // position the dropdown
    var top = this.filter_btn.offset().top + this.filter_btn.height();
    var left = this.filter_btn.offset().left;

    var filter_width = this.filter_elem.width();
    this.filter_elem.width(filter_width);
    var elem_right = left + filter_width;

    var qgrid_area = this.filter_elem.closest('.q-grid-container');
    if (elem_right > qgrid_area.offset().left + qgrid_area.width()) {
      left = (this.filter_btn.offset().left + this.filter_btn.width()) - filter_width;
    }

    this.filter_elem.offset({top: 0, left: 0});
    this.filter_elem.offset({top: top, left: left});
  }

  hide_filter() {
    if (!this.filter_elem)
      return;
    if (this.disabled_tooltip_showing) {
      this.filter_elem.remove();
      this.filter_elem = null;
      this.disabled_tooltip_showing = false;
    } else if (!this.filter_elem.hasClass("hidden")) {
      this.filter_elem.remove();
      this.filter_elem = null;
    }
    this.filter_btn.removeClass("active");
    this.column_header_elem.removeClass("active");
    this.prev_column_separator.removeClass("active");
  }

  initialize_controls() {
    this.filter_elem.find("a.reset-link").click(
        (e) => this.reset_filter()
    );
    this.filter_elem.find("i.close-button").click(
        (e) => this.hide_filter()
    );
    $(document.body).bind("mousedown",
        (e) => this.handle_body_mouse_down(e)
    );
    $(document.body).bind("keyup",
        (e) => this.handle_body_key_up(e)
    );
  }

  send_filter_changed() {
    if (this.is_active()){
      this.filter_btn.addClass("filter-active");
    } else {
      this.filter_btn.removeClass("filter-active");
    }

    var msg = {
      'type': 'change_filter',
      'field': this.field,
      'filter_info': this.get_filter_info()
    };
    this.widget_model.send(msg);
  }

  handle_body_mouse_down(e) {
    if (this.filter_elem && this.filter_elem[0] != e.target && !$.contains(this.filter_elem[0], e.target) &&
        !$.contains(this.filter_btn[0], e.target) &&
        $(e.target).closest(".filter-child-elem").length == 0) {
      this.hide_filter();
    }
    return true;
  }

  handle_body_key_up(e) {
    if (e.keyCode == 27) { // esc key
      this.hide_filter();
    }
  }

  reset_filter() {
    throw new Error("not implemented!");
  }

  get_filter_info() {
    throw new Error("not implemented!");
  }
}

module.exports = {'FilterBase': FilterBase};
