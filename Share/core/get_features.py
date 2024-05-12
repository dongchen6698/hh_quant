import sys
sys.path.append('../')

import warnings
warnings.filterwarnings("ignore")

import os
import pandas as pd
import numpy as np
import akshare as ak
import sqlite3
import matplotlib.pyplot as plt
# %matplotlib inline

from datetime import datetime
from dateutil.relativedelta import relativedelta
from tqdm import tqdm
from database.downloader.downloader_base import DownloaderBase
import database.database_config as db_config


def init_database():
    """
    初始化数据库操作，
    Todo:需要每天更新当天的训练数据

    Returns:
        _type_: _description_
    """

    db_conn = sqlite3.connect('../database/hh_quant.db')
    db_downloader = DownloaderBase(db_conn, db_config)
    proprocessor = PreProcessing(db_downloader=db_downloader)

    return proprocessor



class PreProcessing:
    def __init__(self, db_downloader:DownloaderBase) -> None:
        self.db_downloader = db_downloader

    def _build_cls_label(self, stock_dataframe):
        """
        明日开始未来N天内优先触发止盈 = 1, 触发止损=2, 其他=0
        """
        def calculate_atr(df, period=14):
            df['high-low'] = df['high'] - df['low']
            df['high-close_prev'] = abs(df['high'] - df['close'].shift(1))
            df['low-close_prev'] = abs(df['low'] - df['close'].shift(1))
            df['tr'] = df[['high-low', 'high-close_prev', 'low-close_prev']].max(axis=1)
            atr = df['tr'].rolling(window=period, min_periods=1).mean()
            return atr

        # 初始化标签参数
        N = 15 # 时间周期
        ATR_period = 14 # ATR计算周期
        ATR_take_profit_factor = 3 # 止盈参数
        ATR_stop_loss_factor = 2 # 止损参数
        # 开始构建标签
        df = stock_dataframe.copy()
        # 1. 计算标签构建所需要的指标
        df['atr'] = calculate_atr(df, period=ATR_period) # 计算每一天的ATR
        df['label'] = 0  # 初始化标签列
        df['return'] = np.NaN # 初始化收益率列
        df['duration'] = np.NaN
        # 2. 轮询判断先止盈还是先止损
        for index in range(len(df)-N):
            buy_price = df.at[index, 'close']
            buy_atr = df.at[index, 'atr'] # 获取目前的ATR
            take_profit_price = buy_price + ATR_take_profit_factor * buy_atr # 提前确定止盈价格
            stop_loss_price = buy_price - ATR_stop_loss_factor * buy_atr # 提前确定止损价格
            for day in range(1, N+1):
                future_day_high = df.at[index+day, 'high'] # 买入后每天的最高价
                future_day_low = df.at[index+day, 'low'] # 买入后每天的最低价
                future_day_close = df.at[index+day, 'close'] # 买入后每天的收盘价
                # 检查价格是否触发止盈或止损条件
                if future_day_high > take_profit_price:
                    df.at[index, 'label'] = 1  # 未来N日走势上升 + 突破止盈
                    df.at[index, 'return'] = (future_day_close / buy_price) - 1
                    df.at[index, 'duration'] = day
                    break  # 退出内循环
                elif future_day_low < stop_loss_price:
                    df.at[index, 'label'] = 2  # 未来N日走势下降 + 突破止损
                    df.at[index, 'return'] = (future_day_close / buy_price) - 1
                    df.at[index, 'duration'] = day
                    break  # 退出内循环
            else:
                df.at[index, 'return'] = (future_day_close / buy_price) - 1
                df.at[index, 'duration'] = day
        # 过滤第二天一字涨停情况
        df = df[df['high'].shift(-1) != df['low'].shift(-1)]
        return df[['datetime', 'label', 'return', 'atr', 'duration']]

    def _process_one_stock(self, stock_code, start_date, end_date):
        stock_base = self.db_downloader._download_stock_base_info(stock_code) # 获取基础代码
        stock_individual = self.db_downloader._download_stock_individual_info(stock_code) # 获取profile信息
        stock_history = self.db_downloader._download_stock_history_info(stock_code, start_date, end_date) # 获取历史行情
        stock_indicator = self.db_downloader._download_stock_indicator_info(stock_code, start_date, end_date) # 获取指标数据
        stock_factor_date = self.db_downloader._download_stock_factor_date_info() # 获取日期特征
        stock_factor_qlib = self.db_downloader._download_stock_factor_qlib_info(stock_code, start_date, end_date) # 获取量价特征
        stock_label = self._build_cls_label(stock_history, ) # 构建Label
        stock_df = stock_base.merge(stock_individual, on=['stock_code']).merge(stock_history, on=['stock_code']).merge(stock_indicator, on=['stock_code', 'datetime']).merge(stock_label, on=['datetime']).merge(stock_factor_date, on=['datetime']).merge(stock_factor_qlib, on=['stock_code', 'datetime']) # 整合数据
        stock_df = stock_base \
            .merge(stock_individual, on=['stock_code', 'stock_name']) \
            .merge(stock_history, on=['stock_code']) \
            .merge(stock_indicator, on=['stock_code', 'datetime']) \
            .merge(stock_label, on=['datetime']) \
            .merge(stock_factor_date, on=['datetime']) \
            .merge(stock_factor_qlib, on=['stock_code', 'datetime']) # 整合数据
        stock_df = stock_df.dropna()
        return stock_df
    
    def _process_all_stock(self, code_type, start_date, end_date):
        # stock_code_list = list(ak.stock_info_a_code_name()['code'].unique()) # 获取A股所有股票列表
        stock_code_list = list(ak.index_stock_cons(code_type)['品种代码'].unique()) # 获取沪深300的股票代码列表
        stock_df_list = []
        for stock_code in tqdm(stock_code_list, desc=f'Process: {code_type} ...'):
            stock_df = self._process_one_stock(stock_code, start_date, end_date)
            if not stock_df.empty:
                stock_df_list.append(stock_df)
        return pd.concat(stock_df_list)


