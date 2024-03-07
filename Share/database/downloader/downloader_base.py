import pandas as pd
from datetime import datetime


class DownloaderBase:
    def __init__(self, db_conn, db_config) -> None:
        self.db_conn = db_conn
        self.db_config = db_config

    def _transfer_datetime(self, datetime_str):
        return datetime.strptime(datetime_str, "%Y%m%d").strftime("%Y-%m-%d")

    def _download_stock_trade_date(self):
        query = f"select * from {self.db_config.TABLE_STOCK_TRADE_DATA_INFO};"
        dataframe = pd.read_sql_query(query, self.db_conn)
        return dataframe

    def _download_stock_base_info(self):
        query = f"select * from {self.db_config.TABLE_STOCK_BASE_INFO};"
        dataframe = pd.read_sql_query(query, self.db_conn)
        return dataframe

    def _download_stock_history_info(self, stock_code, start_date="19700101", end_date="20500101"):
        query = f"select * from {self.db_config.TABLE_STOCK_HISTORY_INFO} where stock_code = '{stock_code}' and datetime between '{self._transfer_datetime(start_date)}' and '{self._transfer_datetime(end_date)}';"
        dataframe = pd.read_sql_query(query, self.db_conn)
        return dataframe

    def _download_stock_factor_date_info(self):
        query = f"select * from {self.db_config.TABLE_STOCK_FACTOR_DATE_INFO};"
        dataframe = pd.read_sql_query(query, self.db_conn)
        return dataframe

    def _download_stock_factor_qlib_info(self, stock_code, start_date="19700101", end_date="20500101"):
        query = f"select * from {self.db_config.TABLE_STOCK_FACTOR_QLIB_INFO} where stock_code = '{stock_code}' and datetime between '{self._transfer_datetime(start_date)}' and '{self._transfer_datetime(end_date)}';"
        dataframe = pd.read_sql_query(query, self.db_conn)
        return dataframe

    def _download_stock_individual_info(self):
        pass

    def _download_stock_event_info(self):
        pass

    def _download_index_history_info(self, index_code, start_date="19700101", end_date="20500101"):
        query = f"select * from {self.db_config.TABLE_INDEX_HISTORY_INFO} where index_code = '{index_code}' and datetime between '{self._transfer_datetime(start_date)}' and '{self._transfer_datetime(end_date)}';"
        dataframe = pd.read_sql_query(query, self.db_conn)
        return dataframe
