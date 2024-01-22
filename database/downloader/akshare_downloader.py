import akshare as ak
import pandas as pd
from datetime import datetime
from tqdm import tqdm


class AkShareDownloader:
    def __init__(self, db_conn, start_date, end_date) -> None:
        self.db_conn = db_conn
        self.start_date = start_date
        self.end_date = end_date

    def _download_stock_trade_date(self):
        table_name = "hh_quant_stock_trade_date_info"
        df = ak.tool_trade_date_hist_sina().rename(
            columns={
                "trade_date": "datetime",
            }
        )
        # 插入数据库
        df.to_sql(table_name, self.db_conn, if_exists="append", index=False)

    def _download_stock_base_info(self):
        table_name = "hh_quant_stock_base_info"
        df = ak.stock_info_a_code_name().rename(
            columns={
                "code": "stock_code",
                "name": "stock_name",
            }
        )
        # 插入数据库
        df.to_sql(table_name, self.db_conn, if_exists="append", index=False)

    def _download_stock_individual_info(self):
        table_name = "hh_quant_stock_individual_info"
        stock_info_list = []
        for stock_code, stock_name in tqdm(ak.stock_info_a_code_name().to_records(index=False), desc="_download_stock_individual_info..."):
            stock_info = ak.stock_individual_info_em(symbol=stock_code)
            if not stock_info.empty:
                stock_info_list.append(stock_info.set_index("item").to_dict()["value"])
        upload_df = pd.DataFrame(stock_info_list).rename(
            columns={
                "总市值": "total_market_cap",
                "流通市值": "circulating_market_cap",
                "行业": "industry",
                "上市时间": "listing_date",
                "股票代码": "stock_code",
                "股票简称": "stock_name",
                "总股本": "total_shares",
                "流通股": "circulating_shares",
            }
        )
        # 插入数据库
        upload_df.to_sql(table_name, self.db_conn, if_exists="append", index=False)

    def _download_stock_history_info(self):
        table_name = "hh_quant_stock_history_info"
        stock_adjust = "hfq"
        for stock_code, stock_name in tqdm(ak.stock_info_a_code_name().to_records(index=False), desc="_download_stock_history_info..."):
            stock_info = ak.stock_zh_a_hist(symbol=stock_code, adjust=stock_adjust, start_date=self.start_date, end_date=self.end_date)
            if not stock_info.empty:
                stock_info = stock_info.rename(
                    columns={
                        "日期": "datetime",
                        "开盘": "open",
                        "最高": "high",
                        "最低": "low",
                        "收盘": "close",
                        "成交量": "volume",
                        "成交额": "turnover",
                        "振幅": "amplitude",
                        "涨跌幅": "change_pct",
                        "涨跌额": "change_amount",
                        "换手率": "turnover_rate",
                    }
                )
                stock_info.insert(0, "stock_adjust", stock_adjust)
                stock_info.insert(0, "stock_name", stock_name)
                stock_info.insert(0, "stock_code", stock_code)
                # 插入数据库
                stock_info.to_sql(table_name, self.db_conn, if_exists="append", index=False)

    def _download_stock_event_info(self):
        table_name = "hh_quant_stock_event_info"
        for trade_date in tqdm(ak.tool_trade_date_hist_sina()["trade_date"], desc="_download_stock_event_info..."):
            current_date = datetime.strftime(trade_date, "%Y%m%d")
            try:
                df = ak.stock_gsrl_gsdt_em(date=current_date)
                if not df.empty:
                    df = df.iloc[:, 1:].rename(
                        columns={
                            "代码": "stock_code",
                            "简称": "stock_name",
                            "事件类型": "event_type",
                            "具体事项": "event_content",
                            "交易日": "datetime",
                        }
                    )
                    # 插入数据库
                    df.to_sql(table_name, self.db_conn, if_exists="append", index=False)
            except TypeError:
                # print(f"TypeError: {current_date}")
                continue


if __name__ == "__main__":
    import sqlite3

    db_conn = sqlite3.connect("database/hh_quant.db")

    start_date = "20000101"
    end_date = "20240101"
    ak_share_downloader = AkShareDownloader(db_conn=db_conn, start_date=start_date, end_date=end_date)
    # ak_share_downloader._download_stock_trade_date()
    # ak_share_downloader._download_stock_base_info()
    # ak_share_downloader._download_stock_individual_info()
    # ak_share_downloader._download_stock_history_info()
    ak_share_downloader._download_stock_event_info()
    db_conn.close()
