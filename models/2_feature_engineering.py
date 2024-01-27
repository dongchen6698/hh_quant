import sqlite3
import pandas as pd
from datetime import datetime, timedelta


class FeatureEngineering:
    def __init__(self, db_conn, start_date, end_date, max_lookback_window=180) -> None:
        self.db_conn = db_conn
        self.start_date = datetime.strftime(datetime.strptime(start_date, "%Y%m%d"), "%Y-%m-%d")
        self.end_date = datetime.strftime(datetime.strptime(end_date, "%Y%m%d"), "%Y-%m-%d")
        # 根据max_lookback_window计算出lookback_start_date
        self.lookback_start_date = datetime.strftime(datetime.strptime(start_date, "%Y%m%d") - timedelta(days=max_lookback_window), "%Y-%m-%d")
        print(f"new_start_date:: {self.lookback_start_date}")

    def _extract_preprocessing_data(self):
        table_name = "hh_quant_stock_preprocessing_result_info"
        self.preprocessing_result = pd.read_sql(f"SELECT * FROM {table_name} WHERE datetime BETWEEN '{self.start_date}' AND '{self.end_date}'", self.db_conn)

    def start():
        pass


if __name__ == "__main__":
    db_conn = sqlite3.connect("database/hh_quant.db")
    preprocessing = FeatureEngineering(db_conn=db_conn, start_date="20050101", end_date="20100101", max_lookback_window=180)
    preprocessing.start()
