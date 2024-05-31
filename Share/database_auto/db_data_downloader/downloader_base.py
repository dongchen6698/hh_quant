import pandas as pd
from datetime import datetime
import sys
import os
import sqlite3

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import database_config as database_config


class DownloaderBase:
    def __init__(self, db_conn, db_config: database_config) -> None:
        self.db_conn = db_conn
        self.db_config = db_config

    def _download_all_stock_info(self, code=None):
        if code:
            query = f"select * from {self.db_config.TABLE_ALL_STOCK_INFO} where code = '{code}';"
        else:
            query = f"select * from {self.db_config.TABLE_ALL_STOCK_INFO};"
        dataframe = pd.read_sql_query(query, self.db_conn)
        return dataframe

    def _download_history_base_info(self, code, start_date=None, end_date=None):
        if start_date and end_date:
            query = f"select * from {self.db_config.TABLE_HISTORY_BASE_INFO} where code = '{code}' and datetime between '{start_date}' and '{end_date}';"
        dataframe = pd.read_sql_query(query, self.db_conn)
        return dataframe

    def _download_history_indicator_info(self, code, start_date=None, end_date=None):
        if start_date and end_date:
            query = f"select * from {self.db_config.TABLE_HISTORY_INDICATOR_INFO} where code = '{code}' and datetime between '{start_date}' and '{end_date}';"
        dataframe = pd.read_sql_query(query, self.db_conn)
        return dataframe

    def _download_history_trade_date(self, start_date=None, end_date=None):
        if start_date and end_date:
            query = f"select * from {self.db_config.TABLE_HISTORY_TRADE_DATE_INFO} where datetime between '{start_date}' and '{end_date}';"
        else:
            query = f"select * from {self.db_config.TABLE_HISTORY_TRADE_DATE_INFO};"
        dataframe = pd.read_sql_query(query, self.db_conn)
        return dataframe

    def _download_history_date_factor_info(self, start_date=None, end_date=None):
        if start_date and end_date:
            query = f"select * from {self.db_config.TABLE_HISTORY_DATE_FACTOR_INFO} where datetime between '{start_date}' and '{end_date}';"
        dataframe = pd.read_sql_query(query, self.db_conn)
        return dataframe

    def _download_history_alpha184_factor_info(self, code, start_date=None, end_date=None):
        if start_date and end_date:
            query = (
                f"select * from {self.db_config.TABLE_HISTORY_ALPHA184_FACTOR_INFO} where code = '{code}' and datetime between '{start_date}' and '{end_date}';"
            )
        dataframe = pd.read_sql_query(query, self.db_conn)
        return dataframe

    def _download_history_alpha101_factor_info(self, code, start_date=None, end_date=None):
        if start_date and end_date:
            query = (
                f"select * from {self.db_config.TABLE_HISTORY_ALPHA101_FACTOR_INFO} where code = '{code}' and datetime between '{start_date}' and '{end_date}';"
            )
        dataframe = pd.read_sql_query(query, self.db_conn)
        return dataframe

    def _download_history_alpha191_factor_info(self, code, start_date=None, end_date=None):
        if start_date and end_date:
            query = (
                f"select * from {self.db_config.TABLE_HISTORY_ALPHA191_FACTOR_INFO} where code = '{code}' and datetime between '{start_date}' and '{end_date}';"
            )
        dataframe = pd.read_sql_query(query, self.db_conn)
        return dataframe
