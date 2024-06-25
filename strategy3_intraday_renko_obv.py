#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jun  3 12:38:21 2024

Strategy 3: Intraday Renko OBV

@author: Muykheng Long
"""
import pandas as pd
import numpy as np
import datetime
import copy
from stocktrends import Renko
import yfinance as yf
import statsmodels.api as sm


def ATR(DF, n=14):
    df = DF.copy()
    df['H-L'] = df['High'] - df['Low']
    df['H-PC'] = df['High'] - df['Adj Close'].shift(1)
    df['L-PC'] = df['Low'] - df['Adj Close'].shift(1)
    df['TR'] = df[['H-L','H-PC','L-PC']].max(axis=1)
    df['ATR'] = df['TR'].rolling(n).mean()
    #   df['ATR'] = df['TR'].ewm(com=n, min_periods=n).mean()
    df2 = df.drop(['H-L','H-PC','L-PC'],axis=1)
    return df2['ATR']

def slope(ser, n):
    "function to calculate slope of n consecutive points on a plot"
    slopes = [i*0 for i in range(n-1)]
    for i in range(n, len(ser)+1):
        y = ser[i-n:i]
        x = np.array(range(n))
        y_scaled = (y - y.min())/(y.max() - y.min())
        x_scaled = (x - x.min())/(x.max() - x.min())
        x_scaled = sm.add_constant(x_scaled)
        model = sm.OLS(y_scaled,x_scaled)
        results = model.fit()
        slopes.append(results.params[-1])
    slope_angle = (np.rad2deg(np.arctan(np.array(slopes))))
    return slope_angle


def renko_DF(DF):
    df = DF.copy()
    df.reset_index(inplace=True)
    df = df.iloc[:,[0,1,2,3,4,6]]
    df.columns = ['date','open','high','low','close','volume']
    df2 = Renko(df)
    df2.brick_size = max(.5, round(ATR(DF,120).iloc[-1],0))
    renko_df = df2.get_ohlc_data()
    renko_df['bar_num'] = np.where(renko_df['uptrend']==True,1,np.where(renko_df['uptrend']==False,-1,0))
    for i in range(1,len(renko_df['bar_num'])):
        if renko_df['bar_num'][i] > 0 and renko_df['bar_num'][i-1] > 0:
            renko_df['bar_num'][i] += renko_df['bar_num'][i-1]
        elif renko_df['bar_num'][i] < 0 and renko_df['bar_num'][i-1] < 0:
            renko_df['bar_num'][i] += renko_df['bar_num'][i-1]
    renko_df.drop_duplicates(subset='date',keep='last',inplace=True)
    return renko_df
 
        
def OBV(DF):
    "function to calculate On Balance Volume"
    df = DF.copy()
    df['daily_return'] = df['Adj Close'].pct_change()
    df['direction'] = np.where(df['daily_return']>=0,1,-1)
    df['direction'][0] = 0
    df['vol_adj'] = df['Volume'] * df['direction']
    df['obv'] = df['vol_adj'].cumsum()
    return df['obv']

def CAGR(DF):
    df = DF.copy()
    df['cum_return'] = (1+df['ret']).cumprod()
    n = len(df)/(252*78)
    CAGR = (df['cum_return'].iloc[-1])**(1/n)-1
    return CAGR

def volatility(DF):
    df = DF.copy()
#    df['ret'] = df['Close'].pct_change()
    vol = df['ret'].std() * np.sqrt(252*78)
    return vol

def sharpe(DF, rf):
    sharpe = (CAGR(DF) - rf)/volatility(DF)
    return sharpe    

def max_dd(DF):
    df = DF.copy()
    df['cum_return'] = (1+df['ret']).cumprod()
    df['cum_rolling_max'] = df['cum_return'].max()
    df['drawdown'] = df['cum_rolling_max'] - df['cum_return']
    return (df['drawdown']/ df['cum_rolling_max']).max()

 
# Download data
tickers = ['MSFT','AAPL','META','AMZN','INTC','CSCO','VZ','IBM','TSLA','AMD'] 

ohlc_intraday = {}

for ticker in tickers: 
    temp = yf.download(ticker,period='1mo',interval='5m')
    temp.dropna(how='any',inplace=True)
    ohlc_intraday[ticker] = temp
    
    
# Merge renko df with original ohlc df
ohlc_renko = {}
df = copy.deepcopy(ohlc_intraday)
tickers_signal = {}
tickers_ret = {}

for ticker in tickers:
    print(f'merging for: {ticker}')
    renko = renko_DF(df[ticker])
    df[ticker]['date'] = df[ticker].index
    ohlc_renko[ticker] = df[ticker].merge(renko.loc[:,['date','bar_num']], how='outer', on='date')
    ohlc_renko[ticker]['bar_num'].fillna(method='ffill', inplace=True)
    ohlc_renko[ticker]['obv'] = OBV(ohlc_renko[ticker])
    ohlc_renko[ticker]['obv_slope'] = slope(ohlc_renko[ticker]['obv'],5)
    tickers_signal[ticker] = ''
    tickers_ret[ticker] = []

    
for ticker in tickers:
    for i in range(len(ohlc_intraday[ticker])):
        ### Check if there is no current trading signal for the ticker
        if tickers_signal[ticker] == '':
            ### Initially, append a return of 0 (no action taken)
            tickers_ret[ticker].append(0)
            # 'Buy' signal is generated if:
            # The Renko bar count is at least 2 (indicating sustained upward movement)
            # The slope of the On Balance Volume (OBV) is greater than 30 degrees (indicating strong buying pressure)
            if (ohlc_renko[ticker]['bar_num'][i] >= 2 and ohlc_renko[ticker]['obv_slope'][i] > 30):
                tickers_signal[ticker] = 'Buy'
            # 'Sell' signal is generated if:
            # The Renko bar count is at most -2 (indicating sustained downward movement)
            # The slope of the OBV is less than -30 degrees (indicating strong selling pressure)
            elif (ohlc_renko[ticker]['bar_num'][i] <= -2 and ohlc_renko[ticker]['obv_slope'][i] < -30):
                tickers_signal[ticker] = 'Sell'
        ### If the current signal is 'Buy'
        elif tickers_signal[ticker] == 'Buy':
            ### Calculate and append the daily return for the current day
            tickers_ret[ticker].append((ohlc_renko[ticker]['Close'][i]/ohlc_renko[ticker]['Close'][i-1]) - 1)
            ### Check if conditions to switch to 'Sell' are met:
            # Renko bar count drops to -2 or lower
            # OBV slope is less than -30
            # This could indicate a strong reversal in price action
            if (ohlc_renko[ticker]['bar_num'][i] <= -2 and ohlc_renko[ticker]['obv_slope'][i] < -30):
                tickers_signal[ticker] = 'Sell'
            ### If Renko bar count drops below 2, reset the signal (close the 'Buy' position)
            elif ohlc_renko[ticker]['bar_num'][i] < 2:
                tickers_signal[ticker] = ''
        ### If the current signal is 'Sell'
        elif tickers_signal[ticker] == 'Sell':
            ### Calculate and append the daily return for the current day
            tickers_ret[ticker].append((ohlc_renko[ticker]['Close'][i]/ohlc_renko[ticker]['Close'][i-1]) - 1)
            ### Check if conditions to switch to 'Buy' are met:
            # Renko bar count rises to 2 or higher
            # OBV slope is greater than 30
            # This could indicate a strong reversal in price action to the upside
            if (ohlc_renko[ticker]['bar_num'][i] >= 2 and ohlc_renko[ticker]['obv_slope'][i] > 30):
                tickers_signal[ticker] = 'Buy'
            ### If Renko bar count rises above -2, reset the signal (close the 'Sell' position)
            elif ohlc_renko[ticker]['bar_num'][i] > -2:
                tickers_signal[ticker] = ''
    ohlc_renko[ticker]['ret'] = np.array(tickers_ret[ticker])
              
               
# Calculate overall strategy's KPI
cagr = {}
sharpe_ratios = {}
max_drawdown = {}
for ticker in tickers:
    print(f'calculating KPIs for {ticker}')
    cagr[ticker] = CAGR(ohlc_renko[ticker])
    sharpe_ratios[ticker] = sharpe(ohlc_renko[ticker], 0.05)
    max_drawdown[ticker] = max_dd(ohlc_renko[ticker])

KPI_df = pd.DataFrame([cagr,sharpe_ratios,max_drawdown],index=['Return','Sharpe Ratio','Max Drawdown'])
KPI_df.T