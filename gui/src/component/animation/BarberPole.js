import React, { Component } from 'react';
import './BarberPole.css';

export default class BarberPole extends Component {
  render() {
    return(
      <div
        className="barberPole"
        style={{'width': this.props.width, 'height': this.props.height}}
      />
    );
  }
}
