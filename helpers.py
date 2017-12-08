from datetime import datetime, timedelta
import requests
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn import preprocessing
from sklearn.linear_model import LinearRegression
from sklearn.svm import SVR
from sklearn.tree import DecisionTreeRegressor


todate = lambda x: datetime.utcfromtimestamp(x / 1000)


def get_data(url, name=None):
    if not name:
        return None
    print('reading %s' % name)
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=365)
    url_path = url % (start_date.strftime('%Y%m%d'), end_date.strftime('%Y%m%d'), name)
    data = requests.get(url_path).json()
    dates = [todate(i[0]) for i in data['data']]
    values = [i[1] for i in data['data']]
    df = pd.DataFrame({'date': dates, 'value': values})
    df = df.set_index('date')
    return df


def generate_features(df):
    df_new = df.copy()

    df_new['value_1'] = df_new['value'].shift(1)
    df_new['avg_price_5'] = pd.rolling_mean(df_new['value'], window=5, min_periods=1).shift(1)
    df_new['avg_price_30'] = pd.rolling_mean(df_new['value'], window=21, min_periods=1).shift(1)
    df_new['avg_price_365'] = pd.rolling_mean(df_new['value'], window=252, min_periods=1).shift(1)
    df_new['ratio_avg_price_5_30'] = df_new['avg_price_5'] / df_new['avg_price_30']
    df_new['ratio_avg_price_5_365'] = df_new['avg_price_5'] / df_new['avg_price_365']
    df_new['ratio_avg_price_30_365'] = df_new['avg_price_30'] / df_new['avg_price_365']

    # standard deviation of prices
    df_new['std_price_5'] = pd.rolling_std(df_new['value'], window=5, min_periods=1).shift(1)

    # rolling_mean calculates the moving standard deviation given a window
    df_new['std_price_30'] = pd.rolling_std(df_new['value'], window=21, min_periods=1).shift(1)
    df_new['std_price_365'] = pd.rolling_std(df_new['value'], window=252, min_periods=1).shift(1)
    df_new['ratio_std_price_5_30'] = df_new['std_price_5'] / df_new['std_price_30']
    df_new['ratio_std_price_5_365'] = df_new['std_price_5'] / df_new['std_price_365']
    df_new['ratio_std_price_30_365'] = df_new['std_price_30'] / df_new['std_price_365']

    # return
    df_new['return_1'] = ((df_new['value'] - df_new['value'].shift(1)) / df_new['value'].shift(1)).shift(1)
    df_new['return_5'] = ((df_new['value'] - df_new['value'].shift(5)) / df_new['value'].shift(5)).shift(1)
    df_new['return_30'] = ((df_new['value'] - df_new['value'].shift(21)) / df_new['value'].shift(21)).shift(1)
    df_new['return_365'] = ((df_new['value'] - df_new['value'].shift(252)) / df_new['value'].shift(252)).shift(1)
    df_new['moving_avg_5'] = pd.rolling_mean(df_new['return_1'], window=5, min_periods=1)
    df_new['moving_avg_30'] = pd.rolling_mean(df_new['return_1'], window=21, min_periods=1)
    df_new['moving_avg_365'] = pd.rolling_mean(df_new['return_1'], window=252, min_periods=1)

    # the target & clean
    # df_new['value'] = df['value']
    df_new = df_new.fillna(0)
    return df_new


def create_featuers_and_label(df, forecast_col, forecast_out):
    df['label'] = df[forecast_col].shift(-forecast_out)
    X = np.array(df.drop(['label'], 1))
    # X = preprocessing.scale(X)
    X_forecast_out = X[-forecast_out:]
    X = X[:-forecast_out]
    y = np.array(df['label'])
    y = y[:-forecast_out]
    return X, y, X_forecast_out

def train_data(X, y, model='linear_regression'):
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size = 0.2)
    if model == 'linear_regression':
        clf = LinearRegression()
    elif model == 'svr':
        clf = SVR(C=1.0, epsilon=0.2)
    elif model == 'decision_tree':
        clf = DecisionTreeRegressor(random_state=0)
    else:
        raise TypeError("model not recognized")
    clf.fit(X_train,y_train)
    accuracy = clf.score(X_test, y_test)
    return clf, accuracy

def predict(clf, X_forecast_out):
    forecast_prediction = clf.predict(X_forecast_out)
    return forecast_prediction