import pandas as pd
from datetime import datetime


class FeatureEngineering:
    def __init__(self, db_conn, start_date, end_date) -> None:
        self.db_conn = db_conn
        self.start_date = datetime.strftime(datetime.strptime(start_date, "%Y%m%d"), "%Y-%m-%d")
        self.end_date = datetime.strftime(datetime.strptime(end_date, "%Y%m%d"), "%Y-%m-%d")

    def _extract_preprocessing_data(self):
        table_name = "hh_quant_stock_preprocessing_result_info"
        self.preprocessing_result = pd.read_sql(f"SELECT * FROM {table_name} WHERE datetime BETWEEN '{self.start_date}' AND '{self.end_date}'", self.db_conn)

    def start():
        pass
