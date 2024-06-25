# Intraday Renko OBV Trading Strategy

This repository contains a Python script for an automated trading strategy based on intraday Renko charts and On Balance Volume (OBV) analysis.

## Features

- **Renko Chart Construction**: Utilizes Renko charts to filter out the noise and focus on substantial price movements.
- **OBV Analysis**: Uses On Balance Volume to assess buying and selling pressure.
- **Trading Signals**: Generates buy and sell signals based on specific criteria involving Renko bar numbers and OBV slopes.
- **Performance Metrics**: Calculates key performance indicators such as Compound Annual Growth Rate (CAGR), volatility, Sharpe ratio, and maximum drawdown.

## Requirements

- Python 3.8.19
- yfinance

Ensure you have the necessary Python packages installed: ```pip install yfinance```

## Strategy Description
- Renko charts are a type of price charting that help filter out minor price movements, focusing only on significant changes. The size of each Renko block is based on the Average True Range (ATR), making it more adaptable to market conditions. In our strategy, a new Renko block is created when the price movement exceeds the ATR-derived threshold.
- OBV is a technical indicator that aggregates volume on up days and subtracts volume on down days to measure buying and selling pressure. It provides a cumulative total and is used to confirm trends.

### Signals
- Buy Signal: A buy signal is triggered when there are at least two consecutive Renko blocks indicating an uptrend combined with an OBV slope greater than 30 degrees, suggesting strong buying pressure.
- Sell Signal: A sell signal is initiated when there are at least two consecutive Renko blocks in a downtrend with an OBV slope less than -30 degrees, indicating strong selling pressure.

### Position Management
The strategy exits a position if the opposite signal is triggered or if the Renko blocks revert back to a neutral state, reducing potential losses from reversals.


## How It Works

- Data Downloading: The script fetches historical intraday data for selected stocks using the yfinance library.
- Renko Chart Calculation: Calculates Renko charts for each stock to determine significant price movements.
- OBV Calculation: Computes the OBV to find trends in volume movements.
- Signal Processing: Analyzes the Renko and OBV data to produce buy and sell signals based on predefined criteria.
- Performance Evaluation: Evaluates the strategy's performance by calculating CAGR, Sharpe ratio, and maximum drawdown.

## Author

Muykheng Long - https://github.com/muykhenglong/
