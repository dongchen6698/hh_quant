import akshare as ak
import pandas as pd
from datetime import datetime
from tqdm import tqdm
import time


class AkShareUploader:
    def __init__(self, db_conn, start_date="20000101", end_date="20500101") -> None:
        self.db_conn = db_conn
        self.start_date = start_date
        self.end_date = end_date

    def _upload_stock_trade_date(self, table_name=None):
        if table_name:
            print(f"开始上传【交易日历】数据到【{table_name}】")
            df = ak.tool_trade_date_hist_sina().rename(
                columns={
                    "trade_date": "datetime",
                }
            )
            # 增量过滤
            existing_check = set([str(i) for i in set(pd.read_sql_query(f"select distinct datetime from {table_name}", self.db_conn)["datetime"].tolist())])
            df = df[~df["datetime"].map(lambda x: str(x) in existing_check)]
            if df.empty:
                print("没有新的【交易日历】数据需要上传。")
            else:
                # 插入数据库
                df.to_sql(table_name, self.db_conn, if_exists="append", index=False)

    def _upload_stock_base_info(self, table_name=None):
        if table_name:
            print(f"开始上传【股票-代码列表】数据到【{table_name}】")
            df = ak.stock_info_a_code_name().rename(
                columns={
                    "code": "stock_code",
                    "name": "stock_name",
                }
            )
            existing_check = set(pd.read_sql_query(f"select distinct stock_code from {table_name}", self.db_conn)["stock_code"].tolist())
            df = df[~df["stock_code"].isin(existing_check)]
            if df.empty:
                print("没有新的【股票-代码列表】数据需要上传。")
            else:
                # 插入数据库
                df.to_sql(table_name, self.db_conn, if_exists="append", index=False)

    def _upload_stock_history_info(self, adjust="hfq", table_name=None):
        if table_name:
            existing_check = set(pd.read_sql_query(f"select distinct stock_code from {table_name}", self.db_conn)["stock_code"].tolist())
            print(len(existing_check))
            print(f"开始上传【股票-行情数据】数据到【{table_name}】")
            for stock_code, stock_name in tqdm(ak.stock_info_a_code_name().to_records(index=False)):
                if stock_code not in existing_check:
                    try:
                        stock_info = ak.stock_zh_a_hist(symbol=stock_code, adjust=adjust, start_date=self.start_date, end_date=self.end_date)
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
                            stock_info.insert(0, "stock_adjust", adjust)
                            stock_info.insert(0, "stock_name", stock_name)
                            stock_info.insert(0, "stock_code", stock_code)
                            # 插入数据库
                            stock_info.to_sql(table_name, self.db_conn, if_exists="append", index=False)
                    except:
                        print(f"{stock_code}_{stock_name} _upload_stock_history_info ERROR...")
                        break

    def _upload_stock_individual_info(self, table_name=None):
        if table_name:
            existing_check = set(pd.read_sql_query(f"select distinct stock_code from {table_name}", self.db_conn)["stock_code"].tolist())
            print(f"开始上传【个股信息】数据到【{table_name}】")
            for stock_code, stock_name in tqdm(ak.stock_info_a_code_name().to_records(index=False)):
                if stock_code not in existing_check:
                    try:
                        stock_info = ak.stock_individual_info_em(symbol=stock_code)
                        if not stock_info.empty:
                            stock_info = pd.DataFrame([stock_info.set_index("item").to_dict()["value"]]).rename(
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
                            stock_info.to_sql(table_name, self.db_conn, if_exists="append", index=False)
                    except:
                        print(f"{stock_code}_{stock_name} _upload_stock_individual_info ERROR...")
                        break

    def _upload_stock_indicator_info(self, table_name=None):
        if table_name:
            existing_check = set(pd.read_sql_query(f"select distinct stock_code from {table_name}", self.db_conn)["stock_code"].tolist())
            print(f"开始上传【个股指标】数据到【{table_name}】")
            for stock_code, stock_name in tqdm(ak.stock_info_a_code_name().to_records(index=False)):
                if stock_code not in existing_check:
                    try:
                        stock_info = ak.stock_a_indicator_lg(symbol=stock_code)
                        if not stock_info.empty:
                            stock_info = stock_info.rename(
                                columns={
                                    "trade_date": "datetime",
                                    "pe": "pe",
                                    "pe_ttm": "pe_ttm",
                                    "pb": "pb",
                                    "ps": "ps",
                                    "ps_ttm": "ps_ttm",
                                    "dv_ratio": "dv_ratio",
                                    "dv_ttm": "dv_ttm",
                                    "total_mv": "total_mv",
                                }
                            )
                            stock_info.insert(0, "stock_name", stock_name)
                            stock_info.insert(0, "stock_code", stock_code)
                            # 插入数据库
                            stock_info.to_sql(table_name, self.db_conn, if_exists="append", index=False)
                    except:
                        print(f"{stock_code}_{stock_name} _upload_stock_indicator_info ERROR...")
                        break

    def _upload_index_base_info(self, table_name=None):
        if table_name:
            print(f"开始上传【指数-代码列表】数据到【{table_name}】")
            df = ak.index_stock_info().rename(
                columns={
                    "index_code": "index_code",
                    "display_name": "index_name",
                    "publish_date": "publish_date",
                }
            )
            # 增量过滤
            existing_check = set(pd.read_sql_query(f"select distinct index_code from {table_name}", self.db_conn)["index_code"].tolist())
            df = df[~df["index_code"].isin(existing_check)]
            if df.empty:
                print("没有新的【指数-代码列表】数据需要上传。")
            else:
                # 插入数据库
                df.to_sql(table_name, self.db_conn, if_exists="append", index=False)

    def _upload_index_history_info(self, table_name=None):
        if table_name:
            existing_check = set(pd.read_sql_query(f"select distinct index_code from {table_name}", self.db_conn)["index_code"].tolist())
            print(f"开始上传【指数数据】数据到【{table_name}】")
            for index_code, index_name, pulish_date in tqdm(ak.index_stock_info().to_records(index=False)):
                if index_code not in existing_check:
                    try:
                        index_info = ak.index_zh_a_hist(symbol=index_code, start_date=self.start_date, end_date=self.end_date)
                        if not index_info.empty:
                            index_info = index_info.rename(
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
                            index_info.insert(0, "index_publish_date", pulish_date)
                            index_info.insert(0, "index_name", index_name)
                            index_info.insert(0, "index_code", index_code)
                            # 插入数据库
                            index_info.to_sql(table_name, self.db_conn, if_exists="append", index=False)
                    except TypeError:
                        print(f"{index_code}_{index_name} _upload_index_history_info TypeError...")
                    except:
                        print(f"{index_code}_{index_name} _upload_index_history_info ERROR...")
                        break

    # def _upload_stock_event_info(self, table_name=None):
    #     if table_name:
    #         print(f"开始上传【股市日历】数据到【{table_name}】")
    #         trade_date_info = ak.tool_trade_date_hist_sina()["trade_date"].apply(lambda x: datetime.strftime(x, "%Y%m%d"))
    #         # candidate_date_info = trade_date_info[(trade_date_info >= start_date) & (trade_date_info <= end_data)]
    #         for current_date in tqdm(trade_date_info, desc="_upload_stock_event_info..."):
    #             try:
    #                 df = ak.stock_gsrl_gsdt_em(date=current_date)
    #                 if not df.empty:
    #                     df = df.iloc[:, 1:].rename(
    #                         columns={
    #                             "代码": "stock_code",
    #                             "简称": "stock_name",
    #                             "事件类型": "event_type",
    #                             "具体事项": "event_content",
    #                             "交易日": "datetime",
    #                         }
    #                     )
    #                     # 插入数据库
    #                     df.to_sql(table_name, self.db_conn, if_exists="append", index=False)
    #             except TypeError:
    #                 continue


# if __name__ == "__main__":
#     import sqlite3

#     db_conn = sqlite3.connect("database/hh_quant.db")

#     start_date = "20000101"
#     end_date = "20240101"
#     ak_share_uploader = AkShareuploader(db_conn=db_conn, start_date=start_date, end_date=end_date)
#     # ak_share_uploader._upload_stock_trade_date()
#     # ak_share_uploader._upload_stock_base_info()
#     # ak_share_uploader._upload_stock_individual_info()
#     # ak_share_uploader._upload_stock_history_info()
#     ak_share_uploader._upload_stock_event_info()
#     db_conn.close()
