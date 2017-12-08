import os
from flask import render_template, request
from flask_api import FlaskAPI, status
import json
from operator import itemgetter
import random

from helpers import *
from bokeh.plotting import figure
from bokeh.io import export_png
from datetime import timedelta
import datetime
from bokeh.models import Range1d
import matplotlib.pyplot as plt


plt.switch_backend('agg')


app = FlaskAPI(__name__)
app.args = {}

api_url = 'https://www.isyatirim.com.tr/_Layouts/15/IsYatirim.Website/Common/ChartData.aspx/IndexHistoricalAll?period=1440&from=%s000000&to=%s235959&endeks=%s.E.BIST'


@app.route('/', methods=['GET'])
def home():
    return render_template('index.html')


@app.route('/stock-names', methods=['GET'])
def stock_names():
    search = request.args.get('search')
    with open(os.path.join('.', 'data', 'stock_names.json')) as f:
        names = json.load(f)
    if search:
        return [x for x in names if search.lower() in x.lower()]
    return names


@app.route('/stock-values', methods=['GET'])
def stock_values():
    index = request.args.get('index')
    if not index:
        return {}, status.HTTP_400_BAD_REQUEST
    data = get_data(api_url, index)
    result = {
        'date': [d.strftime('%Y-%m-%d') for d in data.index.tolist()],
        'value': data.value.tolist()
    }
    return result


@app.route('/forecast', methods=['POST'])
def forecast():
    index_name = request.json.get('index_name', 'KCHOL')
    head = int(request.json.get('head', '1'))
    data = get_data(api_url, index_name)
    data = generate_features(data)
    X, y, X_forecast_out = create_featuers_and_label(data, 'value', head)
    lr, lr_accuracy = train_data(X, y)
    svr, svr_accuracy = train_data(X, y, 'svr')
    dt, dt_accuracy = train_data(X, y, 'decision_tree')
    models = [
        {
            'name': 'Linear Regression',
            'accuracy': lr_accuracy,
            'fitted_model': lr
        },
        {
            'name': 'Support Vector Regression',
            'accuracy': svr_accuracy,
            'fitted_model': svr
        },
        {
            'name': 'Decision Tree',
            'accuracy': dt_accuracy,
            'fitted_model': dt
        }
    ]
    sorted_models = sorted(models, key=itemgetter('accuracy'), reverse=True)
    best_model = sorted_models[0]
    predictions = predict(best_model['fitted_model'], X_forecast_out)
    if predictions.any():
        predictions = predictions.round(3)
    start_date = data.iloc[-1].name + timedelta(days=1)
    rng = pd.date_range(start=start_date, periods=head)

    graph_name = '%s_graph.png' % int(random.random() * 1000000)
    data['forecast'] = np.nan
    # plot
    last_date = data.iloc[-1].name
    last_unix = last_date.timestamp()
    one_day = 86400
    next_unix = last_unix + one_day

    for i in predictions:
        next_date = datetime.datetime.fromtimestamp(next_unix)
        next_unix += 86400
        data.loc[next_date] = [np.nan for _ in range(len(data.columns)-1)]+[i]
    data['value'].plot(figsize=(15,6), color="green")
    data['forecast'].plot(figsize=(15,6), color="orange")
    plt.legend(loc=4)
    plt.xlabel('Date')
    plt.ylabel('Price')
    plt.savefig(os.path.join(os.curdir, 'static', 'img', graph_name))


    dates = [d.strftime('%Y-%m-%d') for d in rng]
    predictions_result = dict(zip(dates, predictions.tolist()))

    result = {
        'predictions': predictions_result,
        'graph': graph_name,
        'models': list(map(lambda x: {'name': x['name'], 'accuracy': round(x['accuracy'], 3)}, sorted_models))
    }
    return result


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')