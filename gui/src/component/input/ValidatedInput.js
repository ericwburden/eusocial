import React, { Component } from 'react';
import classNames from 'classnames'

export default class ValidatedInput extends Component {
  constructor(props) {
    super(props)
    this.handleChange = this.handleChange.bind(this);
  }

  handleChange(event) {
    const target = event.target;
    const value = target.value;
    const name = target.id;
    const isValid = this.validateField(value)

    this.props.onFieldChange(name, value, isValid)
  }

  validateField(value) {
    let required = this.props.required;
    let pattern = this.props.validationPattern;
    let isValid = this.props.inputValid;

    if (pattern && required) {
      isValid = RegExp(pattern).test(value.toString().replace(/-/g, ''));
    } else if (required) {
      isValid = value.length > 0;
    } else if (pattern) {
      isValid = value === '' ? null : RegExp(pattern).test(value.toString().replace(/-/g, ''))
    } else {
      isValid = null
    }

    return(isValid);
  }

  updateFieldValidation = () => {
    this.props.formValidationCallback(this.props.inputValid);
  }

  render() {
    let required = this.props.required;
    let isValid = this.props.inputValid;
    let type = this.props.type;
    let name = this.props.name;
    let label = this.props.label;
    let placeholder = this.props.placeholder;
    let message = this.props.validationWarning;
    let value = this.props.value;
    var srValue = '(not required)'

    var formGroupClassNames = classNames({
      'form-group': true,
      'required': required,
      'has-feedback': true,
      'has-success': isValid && isValid != null,
      'has-error': !isValid && isValid != null,
    });

    var formGroupGlyphClassNames = classNames({
      'glyphicon': true,
      'form-control-feedback': true,
      'glyphicon-ok': isValid && isValid != null,
      'glyphicon-remove': !isValid && isValid != null
    });

    var validationMessageClassNames = classNames({
      'text-danger': true,
      'hidden': isValid || isValid == null
    });

    if (required) {
      srValue = isValid ? '(success)' : '(error)'
    }

    return(
      <div className={formGroupClassNames}>
        <label htmlFor={name}>{label}</label>
        <input
          type={type}
          className="form-control"
          id={name}
          name={name}
          required={required}
          describedby={name + "Status"}
          onChange={(event) => this.handleChange(event)}
          placeholder={placeholder}
          value={value}
        />
        <span className={formGroupGlyphClassNames} aria-hidden="true"></span>
        <span id={name + "Status"} className="sr-only">{srValue}</span>
        <small className={validationMessageClassNames}>{message}</small>
      </div>
    );
  }
}
