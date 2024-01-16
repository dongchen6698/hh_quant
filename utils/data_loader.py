import akshare as ak
import pandas as pd
import backtrader as bt
from datetime import datetime


def load_data(symbol, start_date=None, end_date=None):
    # 选取数据的前6列适配backtrader数据格式
    stock_hfq_df = ak.stock_zh_a_hist(symbol=symbol, adjust="hfq", start_date=start_date, end_date=end_date).iloc[:, :6]
    if not stock_hfq_df.empty:
        stock_hfq_df.columns = ["date", "open", "close", "high", "low", "volume"]
        stock_hfq_df.index = pd.to_datetime(stock_hfq_df["date"])
        start_date = datetime.strptime(start_date, "%Y%m%d")
        end_date = datetime.strptime(end_date, "%Y%m%d")
        data = bt.feeds.PandasData(dataname=stock_hfq_df, fromdate=start_date, todate=end_date)  # 规范化数据格式
        return data
    return None


def load_candidates(stock_symbols, stock_symbol_prefix=None):
    full_stock = ak.stock_zh_a_spot_em()[["代码", "名称"]]
    if stock_symbols:
        full_stock = full_stock[full_stock["代码"].isin(stock_symbols)]
    if stock_symbol_prefix is not None:
        full_stock = full_stock[full_stock["代码"].str.startswith(stock_symbol_prefix)]
    return full_stock.to_records(index=False)
