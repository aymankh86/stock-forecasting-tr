import os
import warnings
from flask import render_template, request
from flask_api import FlaskAPI, status
import json
from operator import itemgetter
import random
import logging

from helpers import *
from bokeh.plotting import figure
from bokeh.io import export_png
from datetime import timedelta
import datetime
from bokeh.models import Range1d
import matplotlib.pyplot as plt


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

warnings.simplefilter(action='ignore', category=FutureWarning)

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
    logger.info("Reading %s stock data from api ...", index_name)
    data = get_data(api_url, index_name)

    logger.info("Extracting %s custom features ...", index_name)
    data = generate_features(data)
    logger.info("%s have %s features", index_name, len(data.columns))

    logger.info("Extracting Train/Test data from %s data ...", index_name)
    X, y, X_forecast_out = create_featuers_and_label(data, 'value', head)

    logger.info("Training models ...")
    lr, lr_accuracy = train_data(X, y)
    logger.info("Trained Linear Regression model with %s accuracy", round(lr_accuracy, 3))

    svr, svr_accuracy = train_data(X, y, 'svr')
    logger.info("Trained Support Vector Regression model with %s accuracy", round(svr_accuracy, 3))

    dt, dt_accuracy = train_data(X, y, 'decision_tree')
    logger.info("Trained Decision Tree model with %s accuracy", round(dt_accuracy, 3))
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
    logger.info("%s model selected as best model to use for forecasting", best_model['name'])

    logger.info("Forecasting %s days...", head)
    predictions = predict(best_model['fitted_model'], X_forecast_out)
    if predictions.any():
        predictions = predictions.round(3)
    start_date = data.iloc[-1].name + timedelta(days=1)
    rng = pd.date_range(start=start_date, periods=head)

    logger.info("Plotting graph...")
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
    plt.legend(loc="upper left")
    plt.xlabel('Date')
    plt.ylabel('Price')
    plt.savefig(os.path.join(os.curdir, 'static', 'img', graph_name))
    plt.cla()
    plt.clf()
    plt.close()



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