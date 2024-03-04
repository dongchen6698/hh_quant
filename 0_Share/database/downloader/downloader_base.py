import pandas as pd


class DownloaderBase:
    def __init__(self, db_conn, db_config) -> None:
        self.db_conn = db_conn
        self.db_config = db_config

    def _download_stock_trade_date(self):
        query = f"select * from {self.db_config.TABLE_STOCK_TRADE_DATA_INFO};"
        dataframe = pd.read_sql_query(query, self.db_conn)
        return dataframe

    def _download_stock_base_info(self):
        query = f"select * from {self.db_config.TABLE_STOCK_BASE_INFO};"
        dataframe = pd.read_sql_query(query, self.db_conn)
        return dataframe

    def _download_stock_history_info(self, stock_code):
        query = f"select * from {self.db_config.TABLE_STOCK_HISTORY_INFO} where stock_code = '{stock_code}';"
        dataframe = pd.read_sql_query(query, self.db_conn)
        return dataframe

    def _download_stock_factor_date_info(self):
        query = f"select * from {self.db_config.TABLE_STOCK_FACTOR_DATE_INFO};"
        dataframe = pd.read_sql_query(query, self.db_conn)
        return dataframe

    def _download_stock_factor_qlib_info(self, stock_code):
        query = f"select * from {self.db_config.TABLE_STOCK_FACTOR_QLIB_INFO} where stock_code = '{stock_code}';"
        dataframe = pd.read_sql_query(query, self.db_conn)
        return dataframe

    def _download_stock_individual_info(self):
        pass

    def _download_stock_event_info(self):
        pass
