import React, { Component } from 'react';
import {
  Grid,
  Row,
  Col,
  Button,
  FormGroup,
  ControlLabel,
  FormControl,
  HelpBlock
} from 'react-bootstrap';
import axios from 'axios';
import CircleBee from '../animation/CircleBee';
import jwt_decode from 'jwt-decode';

class Login extends Component {
  constructor(props) {
    super(props)
    this.state = {
      userText: '',
      passText: '',
      authenticating: false,
      wrongPassword: false,
      noUser: false
    };

    this.handleChange = this.handleChange.bind(this);
    this.handleSubmit = this.handleSubmit.bind(this);
  }

  validateForm() {
    return this.state.username.length > 0 && this.state.password.length > 0;
  }

  handleChange(event) {
    this.setState({
      [event.target.id]: event.target.value,
      'wrongPassword': false,
      'noUser': false
    });
  }

  handleSubmit(event) {
    let self = this;
    const userText = this.state.userText;
    const passText = this.state.passText;
    let onSubmitLogin = this.props.onSubmitLogin;
    event.preventDefault();

    this.setState({'authenticating': true})

    axios
      .post(
        'http://127.0.0.1:5000/login',
        {username: userText, password: passText},
        {headers: {'Content-Type': 'application/json'}}
      )
      .then(function(response) {
        console.log(response)
        if (response.data.message === 'no_user') {
          self.setState({
            'authenticating': false,
            'noUser': true,
            'passText': ''
          });
        } else if (response.data.message === 'fail'){
          self.setState({
            'authenticating': false,
            'wrongPassword': true,
            'passText': ''
          });
        } else {
          const decoded_jwt = jwt_decode(response.data.access_token)
          const user_claims = decoded_jwt.user_claims;
          localStorage.setItem('access_token', response.data.access_token)
          localStorage.setItem('refresh_token', response.data.refresh_token)
          onSubmitLogin(
            response.data.username,
            user_claims.role,
            true
          )
        }
      })
      .catch(function(error) {
        console.log(error);
        //TODO Handle Errors
      });
  }

  renderHelpMessage() {
    if (this.state.wrongPassword) {
      return(
        'Sorry, that password is not valid for that username.'
      );
    } else if (this.state.noUser) {
      return(
        'No registered users with that username.'
      );
    }
  }

  renderLoginForm() {
    if (this.state.authenticating) {
      return(
        <div style={{
          'position': 'static',
          'background': 'white',
          'top': '0px',
          'left': '-1px',
          'height': '185px',
          'width': '230px',
        }}>
          <div style={{
            'position': 'relative',
            'width': '100%',
            'textAlign': 'center',
            'height': '0px'
          }}>
            <h5>Authenticating...</h5>
          </div>
          <CircleBee />
        </div>
      );
    } else {
      return(
        <form onSubmit={this.handleSubmit}>
          <FormGroup controlId='userText'>
            <ControlLabel>Username:</ControlLabel>
            <FormControl
              type="text"
              value={this.state.userText}
              placeholder="your.name@agency.org"
              onChange={this.handleChange}
              required={true}
            />
            <FormControl.Feedback />
          </FormGroup>

          <FormGroup controlId='passText'>
            <ControlLabel>Password:</ControlLabel>
            <FormControl
              type="password"
              value={this.state.passText}
              onChange={this.handleChange}
              required={true}
            />
            <FormControl.Feedback />
            <HelpBlock>
              <span className='text-danger'>
                {this.renderHelpMessage()}
              </span>
            </HelpBlock>
          </FormGroup>
          <Button type="submit" bsStyle='primary'>Sign In</Button>
        </form>
      );
    }
  }

  render() {
    return(
      <Grid fluid>
        <Row>
          <Col style={{borderRight: '1px solid silver'}} xs={6}>
            {this.renderLoginForm()}
          </Col>
          <Col xs={6}>
            <p>No account? Request one from your administrator here:</p>
            <Button bsStyle='primary'>Request Account</Button>
          </Col>
        </Row>
      </Grid>
    );
  }
}

export default Login;
