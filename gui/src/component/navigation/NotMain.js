import React, { Component } from 'react';
import {Grid, Row, Col} from 'react-bootstrap';

class NotMain extends Component {
  render() {
    return(
      <Grid fluid>
        <Row>
          <Col xs={12} xsOffset={0} sm={10} smOffset={1}>
            <p>
              Goodbye World!
            </p>
          </Col>
        </Row>
      </Grid>
    );
  }
}

export default NotMain;
