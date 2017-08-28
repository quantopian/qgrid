/**
 * Input handlers
 *
 * Adapted from https://github.com/mleibman/SlickGrid/blob/master/slick.editors.js
 * MIT License, Copyright (c) 2010 Michael Leibman
 */
var $ = require('jquery');
var jquery_ui = require('jquery-ui');

class DateEditor {
  constructor(args) {
    var $input;
    var defaultValue;
    var scope = this;
    var calendarOpen = false;
    this.init = () => {
      $input = $("<input type=text class='editor-text' />");
      $input.appendTo(args.container);
      $input.focus().select();
      $input.datepicker({
        showOn: "button",
        buttonImageOnly: true,
        beforeShow: () => {
          calendarOpen = true;
        },
        onClose: () => {
          calendarOpen = false;
        }
      });

      $input.width($input.width() - 18);
    };

    this.destroy = () => {
      $.datepicker.dpDiv.stop(true, true);
      $input.datepicker("hide");
      $input.datepicker("destroy");
      $input.remove();
    };

    this.show = () => {
      if (calendarOpen) {
        $.datepicker.dpDiv.stop(true, true).show();
      }
    };

    this.hide = () => {
      if (calendarOpen) {
        $.datepicker.dpDiv.stop(true, true).hide();
      }
    };

    this.position = (position) => {
      if (!calendarOpen) {
        return;
      }
      $.datepicker.dpDiv
          .css("top", position.top + 30)
          .css("left", position.left);
    };

    this.focus = () => {
      $input.focus();
    };

    this.loadValue = (item) => {
      defaultValue = item[args.column.field];
      $input.val(defaultValue);
      $input[0].defaultValue = defaultValue;
      $input.select();
    };

    this.serializeValue = () => {
      return $input.val();
    };

    this.applyValue = (item, state) => {
      item[args.column.field] = state;
    };

    this.isValueChanged = () => {
      return (!($input.val() == "" && defaultValue == null)) && ($input.val() != defaultValue);
    };

    this.validate = () => {
      return {
        valid: true,
        msg: null
      };
    };

    this.init();
  }
}

class TextEditor {
  constructor(args) {
    var $input;
    var defaultValue;
    var scope = this;

    this.init = () => {
      $input = $("<input type=text class='editor-text' />")
          .appendTo(args.container)
          .bind("keydown.nav", (e) => {
            if (e.keyCode === $.ui.keyCode.LEFT || e.keyCode === $.ui.keyCode.RIGHT) {
              e.stopImmediatePropagation();
            }
          })
          .focus()
          .select();
    };

    this.destroy = () => {
      $input.remove();
    };

    this.focus = () => {
      $input.focus();
    };

    this.getValue = () => {
      return $input.val();
    };

    this.setValue = (val) => {
      $input.val(val);
    };

    this.loadValue = (item) => {
      defaultValue = item[args.column.field] || "";
      $input.val(defaultValue);
      $input[0].defaultValue = defaultValue;
      $input.select();
    };

    this.serializeValue = () => {
      return $input.val();
    };

    this.applyValue = (item, state) => {
      item[args.column.field] = state;
    };

    this.isValueChanged = () => {
      return (!($input.val() == "" && defaultValue == null)) && ($input.val() != defaultValue);
    };

    this.validate = () => {
      if (args.column.validator) {
        var validationResults = args.column.validator($input.val());
        if (!validationResults.valid) {
          return validationResults;
        }
      }

      return {
        valid: true,
        msg: null
      };
    };

    this.init();
  }
}

//  http://stackoverflow.com/a/22118349
class SelectEditor {
  constructor(args) {
    var $select;
    var defaultValue;
    var scope = this;
    var options = [];

    this.init = () => {
      if (args.column.editorOptions.options) {
        options = args.column.editorOptions.options.split(',');
      } else {
        options = "yes,no".split(',');
      }
      var option_str = "";
      for (var i in options) {
        var opt = $.trim(options[i]); // remove any white space including spaces after comma
        option_str += "<OPTION value='" + opt + "'>" + opt + "</OPTION>";
      }
      $select = $("<SELECT tabIndex='0' class='editor-select'>" + option_str + "</SELECT>");
      $select.appendTo(args.container);
      $select.focus();
    };

    this.destroy = () => {
      $select.remove();
    };

    this.focus = () => {
      $select.focus();
    };

    this.loadValue = (item) => {
      defaultValue = item[args.column.field];
      $select.val(defaultValue);
    };

    this.serializeValue = () => {
      if (args.column.editorOptions.options) {
        return $select.val();
      } else {
        return ($select.val() == "yes");
      }
    };

    this.applyValue = (item, state) => {
      item[args.column.field] = state;
    };

    this.isValueChanged = () => {
      return ($select.val() != defaultValue);
    };

    this.validate = () => {
      return {
        valid: true,
        msg: null
      };
    };

    this.init();
  }
}

/**
 * Validator for numeric cells.
 */
var validateNumber = (value) => {
  if (isNaN(value)) {
    return {
      valid: false,
      msg: "Please enter a valid integer"
    };
  }
  return {
    valid: true,
    msg: null
  };
};

module.exports = {
  'DateEditor': DateEditor,
  'TextEditor': TextEditor,
  'validateNumber': validateNumber,
  'SelectEditor': SelectEditor
};
