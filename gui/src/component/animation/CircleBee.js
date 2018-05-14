import React, { Component } from 'react';
import './CircleBee.css';
import bee from '../img/eusocial_bee_only.svg';

export default class CircleBee extends Component {
  render() {
    return(
      <div id="CircleBeeContainer">
        <div id="CircleBeeOrbit">
          <img src={bee} className="CircleBeeImg" alt='Loading' />
        </div>
      </div>
    );
  }
}
