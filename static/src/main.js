import React, { Component } from 'react'
import ReactDOM from 'react-dom'
import Index from './components/Index'


class App extends Component {
  render() {
    return (
        <div>
          <div className="content-wrapper">
            <section className="content">
              <Index />
            </section>
          </div>
        </div>
    )
  }
}

ReactDOM.render(<App />, document.getElementById('content'));