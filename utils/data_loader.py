import akshare as ak
import pandas as pd
import backtrader as bt
from datetime import datetime


def load_backtest_data(symbols, start_date=None, end_date=None):
    stock_candidates = ak.stock_info_a_code_name()
    if symbols:
        stock_candidates = stock_candidates[stock_candidates["code"].isin(symbols)]
    data_dict = {}
    for stock_code, stock_name in stock_candidates.to_records(index=False):
        stock_hfq_df = ak.stock_zh_a_hist(symbol=stock_code, adjust="hfq", start_date=start_date, end_date=end_date).iloc[:, :6]
        if not stock_hfq_df.empty:
            stock_hfq_df.columns = ["date", "open", "close", "high", "low", "volume"]
            stock_hfq_df.index = pd.to_datetime(stock_hfq_df["date"])
            start_date = datetime.strptime(start_date, "%Y%m%d")
            end_date = datetime.strptime(end_date, "%Y%m%d")
            stock_hfq_data_feed = bt.feeds.PandasData(dataname=stock_hfq_df, fromdate=start_date, todate=end_date)  # 规范化数据格式
            data_dict[stock_name] = stock_hfq_data_feed
    return data_dict
