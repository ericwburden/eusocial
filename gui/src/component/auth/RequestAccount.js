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

export default class RequestAccout extends Component {
  constructor(props) {
    super(props);
    this.state = {
      emailText: '',
      programSelection: ''
    }
  }
}
