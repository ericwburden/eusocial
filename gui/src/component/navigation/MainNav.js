import React, { Component } from 'react';
import { withRouter } from 'react-router-dom';
import {
  Navbar,
  Nav,
  NavItem,
  NavDropdown,
  MenuItem,
  Grid,
  Row,
  Col,
  Modal,
  Button
} from 'react-bootstrap';
import jwt_decode from 'jwt-decode';
import Login from '../auth/Login';

class MainNav extends Component {
  constructor(props) {
    super(props)
    this.state = {
      authenticated: false,
      username: '',
      userRole: '',
      loginModal: false
    }

    this.toggleLoginModal = this.toggleLoginModal.bind(this);
    this.handleLogin = this.handleLogin.bind(this);
    this.handleLogout = this.handleLogout.bind(this);
  }

  handleLogin(username, role, authenticated) {
    this.setState({
      'username': username,
      'userRole': role,
      'authenticated': authenticated
    })

    const access_token = localStorage.getItem('access_token');
    if(access_token != null) {
      this.toggleLoginModal();
    }
  }

  handleLogout() {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    this.forceUpdate();
    alert('Logging out!');
  }

  toggleLoginModal() {
    const access_token = localStorage.getItem('access_token');
    if (access_token != null && !this.state.loginModal) {
      alert('You are already logged in')
    } else {
      this.setState({'loginModal': !this.state.loginModal})
    }
  }

  renderLoginModal() {
    if (this.state.loginModal) {
      return(
        <div className="static-modal">
          <Modal.Dialog>
            <Modal.Header>
              <Modal.Title>Log In</Modal.Title>
            </Modal.Header>
            <Modal.Body><Login onSubmitLogin={this.handleLogin} /></Modal.Body>
            <Modal.Footer>
              <Button onClick={this.toggleLoginModal}>Close</Button>
            </Modal.Footer>
          </Modal.Dialog>
        </div>
      );
    } else {
      return(null);
    }
  }

  renderAdminAuthLink(isAuthenticated, role) {
    if(isAuthenticated && role === 'admin') {
      return(
        withRouter(({ history }) => (
           <MenuItem eventKey={4.1} onClick={() => { history.push('/not') }}>
             Admin
           </MenuItem>
         ))
      );
    } else {
      return(null);
    }
  }

  renderAuthLink() {
    const access_token = localStorage.getItem('access_token');
    if (access_token != null) {
      const decoded_jwt = jwt_decode(access_token);
      const role = decoded_jwt.user_claims.role;
      console.log(role);
      return(
        <NavDropdown
          eventKey={4}
          title={decoded_jwt.identity}
          id="basic-nav-dropdown"
        >
          {this.renderAdminAuthLink(access_token!= null, role)}
          <MenuItem eventKey={4.2} onClick={this.handleLogout}>
            Log Out
          </MenuItem>
        </NavDropdown>
      );
    } else {
      return(
        <NavItem eventKey={1} href="#" onClick={this.toggleLoginModal}>
          <span>Log In/Register</span>
        </NavItem>
      );
    }
  }

  render() {
    return(
      <Navbar fluid collapseOnSelect>
        <Grid fluid>
          <Row>
            <Col xs={12} xsOffset={0} sm={10} smOffset={1}>
              <Navbar.Header>
                <Navbar.Brand>
                  <a href="#brand">Eusocial</a>
                </Navbar.Brand>
                <Navbar.Toggle />
              </Navbar.Header>
              <Navbar.Collapse>
                <Nav>
                  <NavItem eventKey={1} href="#">
                    Link
                  </NavItem>
                  <NavItem eventKey={2} href="#">
                    Link
                  </NavItem>
                  <NavDropdown
                    eventKey={3}
                    title="Dropdown"
                    id="basic-nav-dropdown"
                  >
                    <MenuItem eventKey={3.1}>Action</MenuItem>
                    <MenuItem eventKey={3.2}>Another action</MenuItem>
                    <MenuItem eventKey={3.3}>Something else here</MenuItem>
                    <MenuItem divider />
                    <MenuItem eventKey={3.3}>Separated link</MenuItem>
                  </NavDropdown>
                </Nav>
                <Nav pullRight>
                  {this.renderAuthLink()}
                </Nav>
              </Navbar.Collapse>
            </Col>
          </Row>
        </Grid>
        {this.renderLoginModal()}
      </Navbar>
    );
  }
}

export default MainNav;
