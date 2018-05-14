import React, { Component } from 'react';
import axios from 'axios';

import './CaseForm.css';
import ValidatedInput from '../input/ValidatedInput'

class CaseForm extends Component {
  constructor(props) {
    super(props)
    this.state = {
      fields: {
        hhFirstName: {
          name: 'hhFirstName',
          value: '',
          isValid: null,
          type: 'text',
          label: 'First Name',
          required: true,
          warning: 'This field is required',
        },
        hhMiddleName: {
          name: 'hhMiddleName',
          value: '',
          isValid: null,
          type: 'text',
          label: 'Middle Name',
        },
        hhLastName: {
          name: 'hhLastName',
          value: '',
          isValid: null,
          type: 'text',
          label: 'Last Name',
          required: true,
          warning: 'This field is required',
        },
        hhDOB: {
          name: 'hhDOB',
          value: '',
          isValid: null,
          type: 'date',
          label: 'Date of Birth',
          required: true,
          warning: 'Please enter a valid date.',
          pattern: '^\\d{8}$'
        },
        hhSSN: {
          name: 'hhSSN',
          value: '',
          isValid: null,
          type: 'text',
          label: 'SSN',
          warning: "Only numbers and dashes allowed. Must include 9 digits.",
          pattern: '^\\d{9}$',
          placeholder: '###-##-####'
        },
        hhPrimaryPhone: {
          name: 'hhPrimaryPhone',
          value: '',
          isValid: null,
          type: 'tel',
          label: 'Primary Phone Number',
          warning: "Only numbers and dashes allowed. Must include 10 digits.",
          pattern: '^\\d{10}',
          placeholder: '###-###-####'
        }
      },
      formValid: false,
    }

    this.handleSubmit = this.handleSubmit.bind(this);
    this.handleFieldChange = this.handleFieldChange.bind(this);
  }

  handleFieldChange(name, value, isValid) {
    const fields = this.state.fields;
    fields[name].value = value;
    fields[name].isValid = isValid;

    this.setState({fields: fields});

    var formValid = true;
    for (var key in fields) {
      if (fields[key].required && !fields[key].isValid) {
        formValid = false;
      }
    }
    this.setState({formValid: formValid});
  }


  handleSubmit(event) {
    const fields = this.state.fields;

    alert('Submitted! Form Valid? ' + this.state.formValid)
    event.preventDefault();

    var formValues = {};
    for (var key in fields) {
      formValues[key] = fields[key].value;
    }
    axios
      .post('http://127.0.0.1:5000/new_case', formValues)
      .then(function(response) {
        console.log(response);
        //TODO Handle responses
      })
      .catch(function(error) {
        console.log(error);
        //TODO Handle Errors
      });
  }

  renderValidatedInput(field) {
    return (
      <ValidatedInput
        type={field.type}
        name={field.name}
        label={field.label}
        required={field.required}
        validationWarning={field.warning}
        validationPattern={field.pattern}
        onFieldChange={this.handleFieldChange}
        inputValid = {field.isValid}
        value = {field.value}
        placeholder = {field.placeholder}
      />
    );
  }

  render() {
    let fields = this.state.fields;

    return (
      <form onSubmit={this.handleSubmit}>
        <div className="panel panel-primary">
          <div className="panel-heading">
            <h4>Head of Household Information</h4>
          </div>
          <div className="panel-body">
            <div className="row">
              <div className="col-xs-4"> {/*hhFirstName*/}
                {this.renderValidatedInput(fields.hhFirstName)}
              </div>
              <div className="col-xs-4"> {/*hhMiddleName*/}
                {this.renderValidatedInput(fields.hhMiddleName)}
              </div>
              <div className="col-xs-4"> {/*hhLastName*/}
                {this.renderValidatedInput(fields.hhLastName)}
              </div>
            </div>
            <div className="row">
              <div className="col-xs-4"> {/*hhDOB*/}
                {this.renderValidatedInput(fields.hhDOB)}
              </div>
              <div className="col-xs-4"> {/*hhSSN*/}
                {this.renderValidatedInput(fields.hhSSN)}
              </div>
              <div className="col-xs-4"> {/*hhPrimaryPhone*/}
                {this.renderValidatedInput(fields.hhPrimaryPhone)}
              </div>
            </div>
            <div className="row"> {/*Button Row*/}
              <div className="col-xs-2">
                <input type="submit" value="Submit" />
              </div>
            </div>
          </div>
        </div>
      </form>
    );
  }
}

export default CaseForm;
