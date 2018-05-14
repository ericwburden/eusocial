import React, { Component } from 'react';
import {BrowserRouter as Router, Route} from 'react-router-dom';

import './App.css';
import MainNav from './component/navigation/MainNav';
import Main from './component/navigation/Main'
import NotMain from './component/navigation/NotMain'

class App extends Component {
  render() {
    return (
      <div>
        <MainNav />
        <Router>
            <div>
              <Route exact path='/' component={Main}/>
              <Route exact path='/not' component={NotMain}/>
            </div>
        </Router>
      </div>
    );
  }
}

export default App;
