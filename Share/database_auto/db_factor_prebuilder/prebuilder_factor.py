import os
import sys

cur_path = os.path.split(os.path.realpath(__file__))[0]
sys.path.append(os.path.abspath(os.path.join(cur_path, "..")))

import json
import pandas as pd
import numpy as np
import akshare as ak
import sys
import database_config as db_config

from tqdm import tqdm
from db_data_downloader.downloader_base import DownloaderBase
from db_factor_prebuilder.utils.expression_excutor import AlphaExpressionExcutor
from datetime import datetime
from dateutil.relativedelta import relativedelta


class PrebuilderFactor:
    def __init__(self, db_conn, db_config: db_config = None, db_downloader: DownloaderBase = None) -> None:
        self.db_conn = db_conn
        self.db_config = db_config
        self.db_downloader = db_downloader
        self.exp_excutor = AlphaExpressionExcutor()  # 表达式引擎

    def _upload_factor_to_db(self, dataframe, table_name, method="append"):
        # 插入数据库
        dataframe.to_sql(table_name, self.db_conn, if_exists=method, index=False)

    def _update_start(self, start_date, end_date):
        # 1. 更新日期相关特征
        self._upload_date_factor(start_date, end_date)
        # 2. 更新Alpha因子特征
        all_stock_info = self.db_downloader._download_all_stock_info()
        stock_list = list(sorted(all_stock_info[all_stock_info["code"].str.startswith(("sh", "sz"))]["code"].unique()))
        # 2.1 更新alpha184因子库
        self._upload_alpha_factor(
            stock_list,
            start_date,
            end_date,
            alpha_dict_path="./db_factor_prebuilder/factor_lib/alpha_184.json",
            db_save_path=self.db_config.TABLE_HISTORY_ALPHA184_FACTOR_INFO,
        )
        # 2.1 更新alpha191因子库
        # self._upload_alpha_factor(
        #     stock_list,
        #     start_date,
        #     end_date,
        #     alpha_dict_path="./db_factor_prebuilder/factor_lib/alpha_191.json",
        #     db_save_path=self.db_config.TABLE_HISTORY_ALPHA191_FACTOR_INFO,
        # )
        # 3. 更新其他特征

    def _upload_date_factor(self, start_date, end_date):
        try:
            print("开始更新日期因子...")
            dataframe = self.db_downloader._download_history_trade_date(start_date, end_date)
            if not dataframe.empty:
                datetime_series = pd.to_datetime(dataframe["datetime"])
                dataframe["weekday"] = datetime_series.dt.weekday  # 星期几（0=星期一，6=星期日）",
                dataframe["day_of_week"] = datetime_series.dt.day_name()  # 星期几的名称",
                dataframe["day_of_month"] = datetime_series.dt.day  # 一个月中的第几天",
                dataframe["month"] = datetime_series.dt.month  # 月份",
                dataframe["season"] = datetime_series.dt.month.map(
                    lambda x: {
                        1: "Winter",
                        2: "Winter",
                        3: "Spring",
                        4: "Spring",
                        5: "Spring",
                        6: "Summer",
                        7: "Summer",
                        8: "Summer",
                        9: "Autumn",
                        10: "Autumn",
                        11: "Autumn",
                        12: "Winter",
                    }.get(x)
                )
                dataframe = dataframe.replace([np.inf, -np.inf], np.nan).dropna()
                self._upload_factor_to_db(dataframe, self.db_config.TABLE_HISTORY_DATE_FACTOR_INFO)
        except KeyboardInterrupt:
            sys.exit(0)
        except Exception as e:
            print(e)

    def _upload_alpha_factor(self, stock_list, start_date, end_date, alpha_dict_path, db_save_path):
        try:
            print("开始更新Alpha因子...")
            alpha_factor_dict = json.loads(open(alpha_dict_path, "r").read())
            new_start_date = datetime.strftime(datetime.strptime(start_date, "%Y-%m-%d") - relativedelta(months=3), "%Y-%m-%d")
            for code in tqdm(stock_list):  # 此处运行需优化
                history_base = self.db_downloader._download_history_base_info(code, new_start_date, end_date)
                # 计算额外的columns
                history_base["ret"] = history_base["close"].pct_change()
                history_base["vwap"] = history_base[["open", "high", "low", "close"]].mean(axis=1)
                # 构建factor
                dataframe = history_base[["code", "datetime"]]
                for alpha_name, alpha_expression in alpha_factor_dict.items():
                    dataframe[alpha_name] = self.exp_excutor.excute(history_base, alpha_expression)
                dataframe = dataframe.replace([np.inf, -np.inf], np.nan)
                dataframe = dataframe[(dataframe["datetime"] >= start_date) & (dataframe["datetime"] <= end_date)]
                self._upload_factor_to_db(dataframe, db_save_path)
        except KeyboardInterrupt:
            sys.exit(0)
        except Exception as e:
            print(e)
