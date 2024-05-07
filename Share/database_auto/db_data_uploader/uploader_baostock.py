import warnings

warnings.filterwarnings("ignore")

import sys
import baostock as bs
import pandas as pd
import numpy as np
from datetime import datetime
from tqdm import tqdm
from db_data_downloader.downloader_base import DownloaderBase


class UploaderBaoStock:
    def __init__(self, db_conn, db_config, db_downloader: DownloaderBase = None) -> None:
        self.db_conn = db_conn
        self.db_config = db_config
        self.db_downloader = db_downloader

    def _bs_login(self):
        #### 登陆系统 ####
        lg = bs.login()
        print(f"login respond error_code: {lg.error_code}, error_msg: {lg.error_msg}")

    def _bs_logout(self):
        #### 登出系统 ####
        bs.logout()

    def _update_all_stock_info(self):
        try:
            df = bs.query_stock_basic().get_data()
            dd = bs.query_stock_industry().get_data()
            if not df.empty and not dd.empty:
                dataframe = df.merge(dd[["code", "code_name", "industry"]], on=["code", "code_name"])
                dataframe = dataframe.rename(
                    columns={
                        "code": "code",
                        "code_name": "code_name",
                        "industry": "industry",
                        "ipoDate": "in_date",
                        "outDate": "out_date",
                        "type": "type",
                        "status": "status",
                    }
                )
                dataframe["industry"] = dataframe["industry"].replace("", "其他")
                dataframe["type"] = dataframe["type"].map(lambda x: {1: "股票", 2: "指数", 3: "其它", 4: "可转债", 5: "ETF"}.get(x, "其他"))
                dataframe["status"] = dataframe["status"].map(lambda x: {1: "上市", 2: "退市"}.get(x, "其他"))
                self._upload_data_to_db(dataframe, self.db_config.TABLE_ALL_STOCK_INFO, method="replace")
        except Exception as e:
            print(e)

    def _update_start(self, start_date, end_date):
        try:
            self._bs_login()  # 登陆bs =============
            # 1. 获取区间内所有的stock信息
            all_stock_set = list(sorted(self.db_downloader._download_all_stock_info()["code"].map(lambda x: x in ("sz", "sh")).unique()))
            # 2. 构建基础数据
            history_base_df = pd.DataFrame()
            history_indicator_df = pd.DataFrame()
            for code in tqdm(all_stock_set):
                history_base_df.append(self._get_history_base_info(code, start_date, end_date))
                history_indicator_df.append(self._get_history_indicator_info(code, start_date, end_date))
            # 3. 更新基础数据
            self._upload_data_to_db(history_base_df, self.db_config.TABLE_HISTORY_BASE_INFO)
            self._upload_data_to_db(history_indicator_df, self.db_config.TABLE_HISTORY_INDICATOR_INFO)
            # 4. 更新交易日历
            trade_date_df = bs.query_trade_dates(start_date=start_date, end_date=end_date).get_data()
            trade_date_list = trade_date_df[trade_date_df["is_trading_day"] == "1"]["calendar_date"].to_list()
            self._upload_data_to_db(pd.DataFrame({"datetime": trade_date_list}), self.db_config.TABLE_HISTORY_TRADE_DATE_INFO)

            self._bs_logout()  # 登出bs =============
        except KeyboardInterrupt:
            sys.exit(0)

    def _upload_data_to_db(self, dataframe, table_name, method="append"):
        # 插入数据库
        dataframe.to_sql(table_name, self.db_conn, if_exists=method, index=False)

    def _get_history_base_info(self, code, start_date, end_date):
        try:
            df = bs.query_history_k_data_plus(
                code=code,
                fields="code,code_name,date,open,high,low,close,volume,amount,turn",
                start_date=start_date,
                end_date=end_date,
                frequency="d",
                adjustflag="1",
            ).get_data()
            if not df.empty:
                df = df.rename(
                    columns={
                        "code": "code",
                        "code_name": "code_name",
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
                for col in ["open", "high", "low", "close", "volume", "amount", "turnover_rate"]:
                    df[col] = df[col].replace("", np.nan)
                    df[col] = df[col].astype("float").round(4)
        except Exception as e:
            print(e)
        return df

    def _get_history_indicator_info(self, code, start_date, end_date):
        try:
            df = bs.query_history_k_data_plus(
                code=code,
                fields="code,code_name,date,peTTM,psTTM,pcfNcfTTM,pbMRQ",
                start_date=start_date,
                end_date=end_date,
                frequency="d",
                adjustflag="1",
            ).get_data()
            if not df.empty:
                df = df.rename(
                    columns={
                        "code": "code",
                        "code_name": "code_name",
                        "date": "datetime",
                        "peTTM": "pe_ttm",
                        "psTTM": "ps_ttm",
                        "pcfNcfTTM": "pcf_ncf_ttm",
                        "pbMRQ": "pb_mrq",
                    }
                )
        except Exception as e:
            print(e)
        return df
