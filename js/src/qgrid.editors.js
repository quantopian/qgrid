/**
 * Input handlers
 *
 * Adapted from https://github.com/mleibman/SlickGrid/blob/master/slick.editors.js
 * MIT License, Copyright (c) 2010 Michael Leibman
 */
var $ = require('jquery');
require('slickgrid-qgrid/slick.editors.js');

class IndexEditor {
  constructor(args){
    this.column_info = args.column;
    this.$cell = $(args.container);
    this.$cell.attr('title',
      'Editing index columns is not supported');
    this.$cell.tooltip();
    this.$cell.tooltip('enable');
    this.$cell.tooltip("open");
    // automatically hide it after 4 seconds
    setTimeout((event, ui) => {
      this.$cell.tooltip('destroy');
      args.cancelChanges();
    }, 3000);
  }

  destroy() {}

  focus() {}

  loadValue(item) {
    this.$cell.text(
        this.column_info.formatter(
            null, null, item[this.column_info.field], this.column_info, null
        )
    );
  }

  serializeValue() {}

  applyValue(item, state) {}

  isValueChanged() {
    return false;
  }

  validate() {
    return {
      valid: true,
      msg: null
    };
  }
}

//  http://stackoverflow.com/a/22118349
class SelectEditor {
  constructor(args) {
    this.column_info = args.column;
    this.options = [];
    if (this.column_info.editorOptions.options) {
      this.options = this.column_info.editorOptions.options;
    } else {
      this.options = ["yes", "no"];
    }
    
    var option_str = "";

    this.elem = $("<SELECT tabIndex='0' class='editor-select'>");

    for (var i in this.options) {
      var opt = $.trim(this.options[i]); // remove any white space including spaces after comma
      var opt_elem = $("<OPTION>");
      opt_elem.val(opt);
      opt_elem.text(opt);
      opt_elem.appendTo(this.elem);
    }

    this.elem.appendTo(args.container);
    this.elem.focus();
  }

  destroy() {
    this.elem.remove();
  }

  focus() {
    this.elem.focus();
  }

  loadValue(item) {
    this.defaultValue = item[this.column_info.field];
    this.elem.val(this.defaultValue);
  }

  serializeValue() {
    if (this.options[0] == "yes") {
      return (this.elem.val() == "yes");
    } else {
      return this.elem.val();
    }
  }

  applyValue(item, state) {
    item[this.column_info.field] = state;
  }

  isValueChanged() {
    return (this.elem.val() != this.defaultValue);
  }

  validate() {
    return {
      valid: true,
      msg: null
    };
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
  'validateNumber': validateNumber,
  'SelectEditor': SelectEditor,
  'IndexEditor': IndexEditor
};
