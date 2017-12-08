import React, { Component } from 'react'
import Select from 'react-select'
import request from 'superagent'
import Loading from 'react-loading'


class Index extends Component {

  constructor(props) {
    super(props)
    this.state = {
      stockName: '',
      stockNames: [],
      forecastOut: 1,
      forecasts: [],
      graph: null,
      models: [],
      loading: false
    }
  }

  handleStockName(e) {
    this.setState({stockName: e ? e.value : e})
  }

  handleOnInputKeyDown(e) {
    if (e.target.value.length > 2) {
      request.get('/stock-names')
        .query({search: e.target.value})
        .end((err, response) => {
          this.setState({stockNames: response.body})
        })
    }
  }

  handleForecastOut(e) {
    this.setState({forecastOut: e.target.value})
  }

  runForecast(e) {
    e.preventDefault()
    request.post('/forecast')
      .send({'index_name': this.state.stockName, head: this.state.forecastOut})
      .end((err, response) => {
        this.setState({forecasts: response.body.predictions,
                       graph: response.body.graph,
                       models: response.body.models,
                       loading: false})
      })
    this.setState({loading: true})
  }

  render() {
    var stockNames = this.state.stockNames.map(x => {
      return {value: x, label: x}
    })

    var resultsDiv = '';
    if (this.state.loading) {
      resultsDiv = <div style={{marginLeft: "40%"}}>running ...<Loading type="spinningBubbles" color="white" /></div>
    }
    if (!this.state.loading && _.keys(this.state.forecasts).length > 0) {
      resultsDiv = <div className='pre-scrollable' style={{border: "1px solid black", padding: 10}}>
                      <label>Models:</label>
                      <ul>
                        {this.state.models.map(
                          item => <li style={{listStyle: 'none', padding: 0, margin: 0}} key={item.name}><label>{item.name}:</label> {item.accuracy}</li>)}
                      </ul>

                      <label>Forecasts:</label>
                      <ul>
                        {_.keys(this.state.forecasts).map(
                          k => <li style={{listStyle: 'none', padding: 0, margin: 0}} key={k}><label>{k}:</label> {this.state.forecasts[k]}</li>)}
                      </ul>
                   </div>
    }

    return (
        <section id="contact">
          <div className="section-content">
            <h1 className="section-header">Stock Prices Forecasting</h1>
            <h3>fill the below form to get forecast values of selected stock</h3>
          </div>
          <div className="contact-section">
          <div className="container">
        <form>
          <div className="col-md-6 form-line">
              <div className="form-group">
                <label htmlFor="exampleInputUsername">Select Stock Name</label>
                <Select
                  id="stockName"
                  style={{width: "100%"}}
                  placeholder="select stock name"
                  options={stockNames}
                  value={this.state.stockName}
                  onInputKeyDown={this.handleOnInputKeyDown.bind(this)}
                  onChange={this.handleStockName.bind(this)}
                  />
              </div>
              <div className="form-group">
                <label htmlFor="exampleInputEmail">Forecast Period</label>
                <input type="number"
                   id="forecastOut"
                   min="1"
                   className="form-control"
                   value={this.state.forecastOut}
                   onChange={this.handleForecastOut.bind(this)} />
              </div>
              <button type="button" onClick={this.runForecast.bind(this)} className="btn btn-default submit">Run Forecast</button>
            </div>
            <div className="col-md-6">
              <div className="form-group">
                <h2>Results</h2>
                <br />
                {this.state.graph ? <a href={"/static/img/" + this.state.graph} target="_blank" className="btn btn-default submit">Open Graph</a> : ''}
                {resultsDiv}
              </div>
              <div>
              </div>
          </div>
        </form>
        </div>
        </div>
    </section>
    )
  }
}

export default Index