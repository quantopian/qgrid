define([
    'jquery',
    'handlebars',
    'filter_base',
    'jqueryui'
], function ($, handlebars, filter_base) {
  "use strict";

  var DateFilter = function(field){
    this.base = filter_base.FilterBase;
    this.base(field);
  }
  DateFilter.prototype = new filter_base.FilterBase;

  DateFilter.prototype.get_filter_template = function(){
    return handlebars.compile(
      "<div class='date-range-filter grid-filter dropdown-menu {{type}}-filter'>" +
        "<h3 class='popover-title'>" +
          "<div class='dropdown-title'>Filter by {{name}}</div>" +
          "<i class='fa fa-times icon-remove close-button'/>" +
        "</h3>" +
        "<div class='dropdown-body'>" +
          "<input class='datepicker ignore start-date'/>" +
          "<span class='to'>to</span>" +
          "<input class='datepicker ignore end-date'/>" +
        "</div>" +
        "<div class='dropdown-footer'>" +
          "<a class='reset-link' href='#'>Reset</a>"+
        "</div>" +
      "</div>"
    );
  }

  DateFilter.prototype.reset_filter = function(){
    this.start_date_control.datepicker("setDate", this.min_date);
    this.end_date_control.datepicker("setDate", this.max_date);
    this.filter_start_date = null;
    this.filter_end_date = null;
  }

  DateFilter.prototype.initialize_controls = function(){
    $.proxy(this.base.prototype.initialize_controls.call(this), this);
    this.max_date = new Date(this.max_value)
    this.min_date = new Date(this.min_value)

    this.start_date_control = this.filter_elem.find(".start-date")
    this.end_date_control = this.filter_elem.find(".end-date")

    var self = this;
    var date_options = {
      "dayNamesMin": ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'],
      "prevText": "",
      "nextText": "",
      minDate: this.min_date,
      maxDate: this.max_date,
      beforeShow: function (input, inst){
        // align the datepicker with the right edge of the input it drops down from
        var clicked_elem = $(inst);
        clicked_elem.closest(".dropdown-menu").addClass("calendar-open");

        var widget = clicked_elem.datepicker('widget');
        widget.css('margin-left', $(input).outerWidth() - widget.outerWidth());
        widget.addClass("stay-open-on-click filter-child-elem");
      },
      onSelect: function (dateText, instance){
        // pull the values from the datepickers
        var start_date_string = self.start_date_control.val();
        var end_date_string = self.end_date_control.val();

        var start_date = new Date(start_date_string);
        var end_date = new Date((new Date(end_date_string).getTime()) + 86399999);

        self.filter_start_date = start_date.getTime();
        self.filter_end_date = end_date.getTime();

        $(self).trigger("filter_changed");

        var datepicker = $(instance.input);
        setTimeout((function(){datepicker.blur();}), 100);

        if (datepicker.hasClass("start-date")){
          // update the end date's min
          self.end_date_control.datepicker("option", "minDate", start_date)
        }
        if (datepicker.hasClass("end-date")){
          // update the start date's max
          self.start_date_control.datepicker("option", "maxDate", new Date(end_date_string))
        }
      }
    }

    this.filter_elem.find(".datepicker").datepicker(date_options)

    this.start_date_control.datepicker("setDate", this.min_date)
    this.end_date_control.datepicker("setDate", this.max_date)
  }

  DateFilter.prototype.is_active = function(){
    return this.filter_start_date || this.filter_end_date;
  }

  DateFilter.prototype.include_item = function(item){
    var cur_row_date = new Date(item[this.field]);
    if (this.filter_start_date){
      if (cur_row_date < new Date(this.filter_start_date)){
        return false;
      }
    }

    if (this.filter_end_date){
      if (cur_row_date > new Date(this.filter_end_date)){
        return false;
      }
    }

    return true;
  }

  return {'DateFilter': DateFilter}
});
