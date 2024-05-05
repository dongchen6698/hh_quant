import sys
import baostock as bs
import pandas as pd
from datetime import datetime
from tqdm import tqdm
import time
import numpy as np
from downloader import DownloaderBase


class BaoStockUploader:
    def __init__(self, db_conn, db_downloader: DownloaderBase = None, start_date="20000101", end_date="20500101") -> None:
        self.db_conn = db_conn
        self.db_downloader = db_downloader
        self.start_date = self._transfer_datetime(start_date)
        self.end_date = self._transfer_datetime(end_date)

    def _transfer_datetime(self, datetime_str):
        return datetime.strptime(datetime_str, "%Y%m%d").strftime("%Y-%m-%d")

    def _upload_stock_history_info(self, table_name=None):
        if table_name:
            stock_code_check = set(pd.read_sql_query(f"select distinct stock_code from {table_name}", self.db_conn)["stock_code"].tolist())
            datetime_check = set(pd.read_sql_query(f"select distinct datetime from {table_name}", self.db_conn)["datetime"].tolist())
            print(f"开始上传【股票-行情数据】数据到【{table_name}】")
            for stock_code, stock_name, stock_prefix in tqdm(self.db_downloader._download_stock_base_info().to_records(index=False)):
                if (stock_code not in stock_code_check) or (self.start_date not in datetime_check):
                    try:
                        stock_info = bs.query_history_k_data_plus(
                            code=stock_prefix + "." + stock_code,
                            fields="code,date,adjustflag,open,high,low,close,volume,amount,turn",
                            start_date=self.start_date,
                            end_date=self.end_date,
                            frequency="d",
                            adjustflag="1",
                        ).get_data()

                        if not stock_info.empty:
                            stock_info = stock_info.rename(
                                columns={
                                    "code": "stock_code",
                                    "adjustflag": "adjust_type",
                                    "date": "datetime",
                                    "open": "open",
                                    "high": "high",
                                    "low": "low",
                                    "close": "close",
                                    "volume": "volume",
                                    "amount": "amount",
                                    "turn": "turnover_rate",
                                }
                            )
                            stock_info["stock_code"] = stock_info["stock_code"].map(lambda x: x.replace(stock_prefix + ".", ""))
                            stock_info["adjust_type"] = stock_info["adjust_type"].map(lambda x: {"1": "后复权", "2": "前复权", "3": "不复权"}.get(x, ""))
                            for col in ["open", "high", "low", "close", "volume", "amount", "turnover_rate"]:
                                stock_info[col] = stock_info[col].replace("", np.nan)
                                stock_info[col] = stock_info[col].astype("float").round(4)
                            # 插入数据库
                            stock_info.to_sql(table_name, self.db_conn, if_exists="append", index=False)
                    except KeyboardInterrupt:
                        print(f"{stock_prefix}{stock_code}_{stock_name} _upload_stock_history_info KeyboardInterrupt...")
                        sys.exit(0)
                    except Exception as e:
                        print(f"{stock_prefix}{stock_code}_{stock_name} _upload_stock_history_info error...{e}")

    def _upload_stock_indicator_info(self, table_name):
        if table_name:
            stock_code_check = set(pd.read_sql_query(f"select distinct stock_code from {table_name}", self.db_conn)["stock_code"].tolist())
            datetime_check = set(pd.read_sql_query(f"select distinct datetime from {table_name}", self.db_conn)["datetime"].tolist())
            print(f"开始上传【个股指标】数据到【{table_name}】")
            for stock_code, stock_name, stock_prefix in tqdm(self.db_downloader._download_stock_base_info().to_records(index=False)):
                if (stock_code not in stock_code_check) or (self.start_date not in datetime_check):
                    try:
                        stock_info = bs.query_history_k_data_plus(
                            code=stock_prefix + "." + stock_code,
                            fields="code,date,peTTM,psTTM,pcfNcfTTM,pbMRQ",
                            start_date=self.start_date,
                            end_date=self.end_date,
                            frequency="d",
                            adjustflag="1",
                        ).get_data()
                        if not stock_info.empty:
                            stock_info = stock_info.rename(
                                columns={
                                    "code": "stock_code",
                                    "date": "datetime",
                                    "peTTM": "pe_ttm",
                                    "psTTM": "ps_ttm",
                                    "pcfNcfTTM": "pcf_ncf_ttm",
                                    "pbMRQ": "pb_mrq",
                                }
                            )
                            stock_info["stock_code"] = stock_info["stock_code"].map(lambda x: x.replace(stock_prefix + ".", ""))
                            # 插入数据库
                            stock_info.to_sql(table_name, self.db_conn, if_exists="append", index=False)
                    except KeyboardInterrupt:
                        print(f"{stock_code}_{stock_name} _upload_stock_indicator_info KeyboardInterrupt...")
                        sys.exit(0)
                    except Exception as e:
                        print(f"{stock_code}_{stock_name} _upload_stock_indicator_info error...{e}")

    def _upload_index_history_info(self, table_name=None):
        if table_name:
            # sh.000016 上证50，sh.000300 沪深300，sh.000905 中证500
            default_index_code_list = ["sh.000016", "sh.000300", "sh.000905"]
            index_code_check = set(pd.read_sql_query(f"select distinct index_code from {table_name}", self.db_conn)["index_code"].tolist())
            datetime_check = set(pd.read_sql_query(f"select distinct datetime from {table_name}", self.db_conn)["datetime"].tolist())
            print(f"开始上传【指数-历史数据】数据到【{table_name}】")
            for index_code in default_index_code_list:
                if (index_code.split(".")[1] not in index_code_check) or (self.start_date not in datetime_check):
                    try:
                        index_info = bs.query_history_k_data_plus(
                            code=index_code,
                            fields="code,date,open,high,low,close,volume,amount",
                            start_date=self.start_date,
                            end_date=self.end_date,
                            frequency="d",
                            adjustflag="1",
                        ).get_data()
                        index_info = index_info.rename(
                            columns={
                                "code": "index_code",
                                "date": "datetime",
                                "open": "open",
                                "high": "high",
                                "low": "low",
                                "close": "close",
                                "volume": "volume",
                                "amount": "amount",
                            }
                        )
                        index_info["index_code"] = index_info["index_code"].map(lambda x: x.replace(index_code.split(".")[0] + ".", ""))
                        for col in ["open", "high", "low", "close", "volume", "amount"]:
                            index_info[col] = index_info[col].replace("", np.nan)
                            index_info[col] = index_info[col].astype("float").round(4)
                        # 插入数据库
                        index_info.to_sql(table_name, self.db_conn, if_exists="append", index=False)
                    except KeyboardInterrupt:
                        print(f"{index_info} _upload_index_history_info KeyboardInterrupt...")
                        sys.exit(0)
                    except Exception as e:
                        print(f"{index_info} _upload_index_history_info error...{e}")

    def _bs_login(self):
        #### 登陆系统 ####
        lg = bs.login()
        # 显示登陆返回信息
        print("login respond error_code:" + lg.error_code)
        print("login respond  error_msg:" + lg.error_msg)

    def _bs_logout(self):
        #### 登出系统 ####
        bs.logout()
