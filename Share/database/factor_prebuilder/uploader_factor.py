import os
import sys

cur_path = os.path.split(os.path.realpath(__file__))[0]
sys.path.append(os.path.abspath(os.path.join(cur_path, "..")))

import json
import pandas as pd
import numpy as np
import akshare as ak
import sys

from tqdm import tqdm
from downloader import DownloaderBase
import sqlite3
from factor_olhcv.expression_excutor import AlphaExpressionExcutor
import database_config as db_config


class FactorUploader:
    def __init__(self, db_conn, db_downloader: DownloaderBase = None, start_date="20000101", end_date="20500101") -> None:
        self.db_conn = db_conn
        self.downloader = db_downloader
        self.start_date = start_date
        self.end_date = end_date

    def _upload_date_factor(self, table_name=None):
        if table_name:
            print(f"开始构建【日期】特征到【{table_name}】")
            dataframe = self.downloader._download_stock_trade_date()  # 获取交易日历信息
            existing_check = set([str(i) for i in set(pd.read_sql_query(f"select distinct datetime from {table_name}", self.db_conn)["datetime"].tolist())])
            dataframe = dataframe[~dataframe["datetime"].map(lambda x: str(x) in existing_check)]
            if dataframe.empty:
                print("没有新的【日期】特征需要构建...")
            else:
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
                # 插入数据库
                dataframe = dataframe.replace([np.inf, -np.inf], np.nan).dropna()
                dataframe.to_sql(table_name, self.db_conn, if_exists="append", index=False)

    def _upload_qlib_factor(self, table_name=None, exp_excutor=None, index_code=None):
        if table_name:
            try:
                print(f"开始构建【qlib因子】特征到【{table_name}】")
                alpha_factor_dict = json.loads(open("./factor_olhcv/alpha_179.json", "r").read())
                existing_check = set(pd.read_sql_query(f"select distinct stock_code from {table_name}", self.db_conn)["stock_code"].tolist())
                if index_code is not None:
                    stock_code_list = set(ak.index_stock_cons(index_code)["品种代码"].tolist())
                else:
                    stock_code_list = set(self.downloader._download_stock_base_info()["stock_code"])
                for stock_code in tqdm(stock_code_list):
                    if stock_code not in existing_check:
                        stock_df = self.downloader._download_stock_history_info(stock_code)
                        dataframe = stock_df[["stock_code", "datetime"]]
                        for alpha_name, alpha_expression in alpha_factor_dict.items():
                            dataframe[alpha_name] = exp_excutor.excute(stock_df, alpha_expression)
                        # 插入数据库
                        dataframe = dataframe.replace([np.inf, -np.inf], np.nan).dropna()
                        dataframe.to_sql(table_name, self.db_conn, if_exists="append", index=False)
            except KeyboardInterrupt:
                sys.exit(0)
            except Exception as e:
                print(f"_upload_qlib_factor error...{e}")


if __name__ == "__main__":
    conn = sqlite3.connect("../hh_quant.db")
    start_date = "20000101"
    end_date = "20231231"
    # 初始化基础信息
    downloader = DownloaderBase(db_conn=conn, db_config=db_config)
    uploader = FactorUploader(db_conn=conn, db_downloader=downloader, start_date=start_date, end_date=end_date)
    exp_excutor = AlphaExpressionExcutor()
    # 开始构建Factor数据
    uploader._upload_date_factor(table_name=db_config.TABLE_STOCK_FACTOR_DATE_INFO)
    uploader._upload_qlib_factor(table_name=db_config.TABLE_STOCK_FACTOR_QLIB_INFO, exp_excutor=exp_excutor, index_code="000300")  # 构建上证50的所有factor
    # 关闭连接
    conn.close()
