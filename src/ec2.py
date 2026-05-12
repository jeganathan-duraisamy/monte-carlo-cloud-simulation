import json
import logging
from flask import Flask, request, jsonify
import yfinance as yf
import pandas as pd
from datetime import date, timedelta
from pandas_datareader import data as pdr

app = Flask(__name__)

logging.basicConfig(level=logging.INFO)

def fetch_stock_data(ticker, start_date, end_date):
    try:
        yf.pdr_override()
        return pdr.get_data_yahoo(ticker, start=start_date, end=end_date)
    except Exception as e:
        logging.error(f"Error fetching data for {ticker}: {e}")
        return None

def identify_signals(stock_data):
    signal_threshold = 0.01
    stock_data['Buy_Signal'] = 0
    stock_data['Sell_Signal'] = 0

    for idx in range(2, len(stock_data)):
        is_three_white_soldiers = (
            (stock_data.Close[idx] - stock_data.Open[idx] >= signal_threshold) and
            (stock_data.Close[idx] > stock_data.Close[idx-1]) and
            (stock_data.Close[idx-1] - stock_data.Open[idx-1] >= signal_threshold) and
            (stock_data.Close[idx-1] > stock_data.Close[idx-2]) and
            (stock_data.Close[idx-2] - stock_data.Open[idx-2] >= signal_threshold)
        )

        is_three_black_crows = (
            (stock_data.Open[idx] - stock_data.Close[idx] >= signal_threshold) and
            (stock_data.Close[idx] < stock_data.Close[idx-1]) and
            (stock_data.Open[idx-1] - stock_data.Close[idx-1] >= signal_threshold) and
            (stock_data.Close[idx-1] < stock_data.Close[idx-2]) and
            (stock_data.Open[idx-2] - stock_data.Close[idx-2] >= signal_threshold)
        )

        if is_three_white_soldiers:
            stock_data.at[stock_data.index[idx], 'Buy_Signal'] = 1

        if is_three_black_crows:
            stock_data.at[stock_data.index[idx], 'Sell_Signal'] = 1

    return stock_data

def perform_simulations(stock_data, params):
    history_window = int(params["history_window"])
    num_simulations = int(params["num_simulations"])
    signal_type = int(params["signal_type"])
    profit_loss_days = int(params["profit_loss_days"])
    
    results = []

    for idx in range(history_window, len(stock_data) - profit_loss_days):
        if (signal_type == 1 and stock_data.Buy_Signal[idx] == 1) or (signal_type == 0 and stock_data.Sell_Signal[idx] == 1):
            avg_return = stock_data.Close[idx-history_window:idx].pct_change(1).mean()
            std_dev = stock_data.Close[idx-history_window:idx].pct_change(1).std()
            simulated_returns = [random.gauss(avg_return, std_dev) for _ in range(num_simulations)]
            simulated_returns.sort(reverse=True)
            var_95 = simulated_returns[int(len(simulated_returns) * 0.95)]
            var_99 = simulated_returns[int(len(simulated_returns) * 0.99)]
            profit_loss = stock_data.Close[idx + profit_loss_days] - stock_data.Close[idx]
            results.append({
                "95%": var_95,
                "99%": var_99,
                "date": stock_data.index[idx].strftime('%Y-%m-%d'),
                "Profit/Loss": profit_loss
            })

    return results

def analyse_market_data(params):
    ticker = 'MSFT'
    current_date = date.today()
    three_years_ago = current_date - timedelta(days=1095)
    
    stock_data = fetch_stock_data(ticker, three_years_ago, current_date)
    if stock_data is None:
        return {"error": "Error fetching stock data"}

    stock_data = identify_signals(stock_data)
    results = perform_simulations(stock_data, params)
    
    return {"data": results}

@app.route('/', methods=['POST'])
def analyse():
    params = request.get_json()
    if not params:
        return jsonify({"error": "Invalid input"}), 400

    analysis_results = analyze_market_data(params)
    return jsonify(analysis_results)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)
