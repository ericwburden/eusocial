import React, { Component } from 'react';
import {Grid, Row, Col} from 'react-bootstrap';

export default class Main extends Component {
  render() {
    return(
      <Grid fluid>
        <Row>
          <Col md={3}>
            <ListGroup>
              <ListGroupItem href="#">Programs</ListGroupItem>
              <ListGroupItem href="#">Link 2</ListGroupItem>
              <ListGroupItem href="#">Link 3</ListGroupItem>
            </ListGroup>
          </Col>
        </Row>
      </Grid>
    );
  }
}
