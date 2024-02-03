class UploaderBase:
    def __init__(self, db_conn) -> None:
        self.db_conn = db_conn

    def _upload_stock_trade_date(self, table_name=None):
        pass

    def _upload_stock_base_info(self, table_name=None):
        pass

    def _upload_stock_individual_info(self, table_name=None):
        pass

    def _upload_stock_history_info(self, start_date, end_date, adjust="qfq", table_name=None):
        pass

    def _upload_stock_event_info(self, start_date, end_data, table_name=None):
        pass
