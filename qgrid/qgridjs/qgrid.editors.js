  /**
   * Input handlers
   *
   * Adapted from https://github.com/mleibman/SlickGrid/blob/master/slick.editors.js
   * MIT License, Copyright (c) 2010 Michael Leibman
   */
  define([
    'jquery',
    'jqueryui'
], function ($) {
  "use strict";

  var DateEditor = function(args) {
      var $input;
      var defaultValue;
      var scope = this;
      var calendarOpen = false;
      this.init = function () {
        $input = $("<INPUT type=text class='editor-text' />");
        $input.appendTo(args.container);
        $input.focus().select();
        $input.datepicker({
          showOn: "button",
          buttonImageOnly: true,
          beforeShow: function () {
            calendarOpen = true
          },
          onClose: function () {
            calendarOpen = false
          }
        });

        $input.width($input.width() - 18);
      };

      this.destroy = function () {
        $.datepicker.dpDiv.stop(true, true);
        $input.datepicker("hide");
        $input.datepicker("destroy");
        $input.remove();
      };

      this.show = function () {
        if (calendarOpen) {
          $.datepicker.dpDiv.stop(true, true).show();
        }
      };

      this.hide = function () {
        if (calendarOpen) {
          $.datepicker.dpDiv.stop(true, true).hide();
        }
      };

      this.position = function (position) {
        if (!calendarOpen) {
          return;
        }
        $.datepicker.dpDiv
            .css("top", position.top + 30)
            .css("left", position.left);
      };

      this.focus = function () {
        $input.focus();
      };

      this.loadValue = function (item) {
        defaultValue = item[args.column.field];
        $input.val(defaultValue);
        $input[0].defaultValue = defaultValue;
        $input.select();
      };

      this.serializeValue = function () {
        return $input.val();
      };

      this.applyValue = function (item, state) {
        item[args.column.field] = state;
      };

      this.isValueChanged = function () {
        return (!($input.val() == "" && defaultValue == null)) && ($input.val() != defaultValue);
      };

      this.validate = function () {
        return {
          valid: true,
          msg: null
        };
      };

      this.init();
  }

  var TextEditor = function(args) {
      var $input;
      var defaultValue;
      var scope = this;

      this.init = function () {
        $input = $("<INPUT type=text class='editor-text' />")
            .appendTo(args.container)
            .bind("keydown.nav", function (e) {
              if (e.keyCode === $.ui.keyCode.LEFT || e.keyCode === $.ui.keyCode.RIGHT) {
                e.stopImmediatePropagation();
              }
            })
            .focus()
            .select();
      };

      this.destroy = function () {
        $input.remove();
      };

      this.focus = function () {
        $input.focus();
      };

      this.getValue = function () {
        return $input.val();
      };

      this.setValue = function (val) {
        $input.val(val);
      };

      this.loadValue = function (item) {
        defaultValue = item[args.column.field] || "";
        $input.val(defaultValue);
        $input[0].defaultValue = defaultValue;
        $input.select();
      };

      this.serializeValue = function () {
        return $input.val();
      };

      this.applyValue = function (item, state) {
        item[args.column.field] = state;
      };

      this.isValueChanged = function () {
        return (!($input.val() == "" && defaultValue == null)) && ($input.val() != defaultValue);
      };

      this.validate = function () {
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

  //  http://stackoverflow.com/a/22118349
  function SelectEditor(args) {
    var $select;
    var defaultValue;
    var scope = this;
    var options = []

    this.init = function() {

        if (args.column.editorOptions.options){
            options = args.column.editorOptions.options.split(',');
        } else {
            options ="yes,no".split(',');
        }
        var option_str = "";
        for (var i in options) {
            var opt = $.trim( options[i] ); // remove any white space including spaces after comma
            option_str += "<OPTION value='" + opt + "'>" + opt + "</OPTION>";
        }
        $select = $("<SELECT tabIndex='0' class='editor-select'>"+ option_str +"</SELECT>");
        $select.appendTo(args.container);
        $select.focus();
    };

    this.destroy = function() {
        $select.remove();
    };

    this.focus = function() {
        $select.focus();
    };

    this.loadValue = function(item) {
      defaultValue = item[args.column.field];
      $select.val(defaultValue);
    };

    this.serializeValue = function() {
        if (args.column.editorOptions.options) {
            return $select.val();
        } else {
            return ($select.val() == "yes");
        }
    };

    this.applyValue = function(item,state) {
        item[args.column.field] = state;
    };

    this.isValueChanged = function() {
        return ($select.val() != defaultValue);
    };

    this.validate = function() {
        return {
            valid: true,
            msg: null
        };
    };

    this.init();
}
  
  /**
   * Validator for numeric cells.
   */
  var validateNumber = function(value) {
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
    }

    return {'DateEditor': DateEditor, 'TextEditor': TextEditor,
            'validateNumber': validateNumber,
            'SelectEditor': SelectEditor};
});
