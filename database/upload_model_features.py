import warnings

warnings.filterwarnings("ignore")
import akshare as ak
import pandas as pd
import pandas_ta as ta
import sqlite3
from tqdm import tqdm


class UploadFromAkToDb:
    def __init__(self, database_conn) -> None:
        self.db_conn = database_conn

    def get_stock_info_records(self):
        return ak.stock_info_a_code_name().to_records(index=False)

    def upload_stock_individual_info(self, if_exists="replace"):
        """
        个股信息数据
        """
        stock_info_list = []
        for stock_code, stock_name in tqdm(self.get_stock_info_records(), desc="upload_stock_individual_info..."):
            stock_info = ak.stock_individual_info_em(symbol=stock_code)
            if not stock_info.empty:
                stock_info_list.append(stock_info.set_index("item").to_dict()["value"])
        upload_df = pd.DataFrame(stock_info_list)
        # 插入数据库
        db_table_name = "hh_quant_stock_individual_info"
        upload_df.to_sql(db_table_name, self.db_conn, if_exists=if_exists, index=False)

    def upload_stock_history_info(self, start_date, end_date, if_exists="append"):
        """
        历史行情数据
        """
        stock_info_list = []
        for stock_code, stock_name in tqdm(self.get_stock_info_records(), desc="upload_stock_history_info..."):
            stock_info = ak.stock_zh_a_hist(symbol=stock_code, adjust="hfq", start_date=start_date, end_date=end_date)
            if not stock_info.empty:
                stock_info.insert(0, "股票简称", stock_name)
                stock_info.insert(0, "股票代码", stock_code)
                stock_info_list.append(stock_info)
        upload_df = pd.concat(stock_info_list)
        # 插入数据库
        db_table_name = "hh_quant_stock_history_info"
        upload_df.to_sql(db_table_name, self.db_conn, if_exists=if_exists, index=False)

    def upload_stock_technical_analysis_info_daily(self, start_date, end_date, if_exists="append"):
        """
        基于历史行情数据的TA指标数据
        """
        stock_info_list = []
        for stock_code, stock_name in tqdm(self.get_stock_info_records(), desc="upload_stock_technical_analysis_info_daily..."):
            try:
                stock_info = ak.stock_zh_a_hist(symbol=stock_code, adjust="hfq", start_date=start_date, end_date=end_date)
                stock_info = stock_info.dropna()
                if not stock_info.empty:
                    stock_info = stock_info.iloc[:, :6]
                    stock_info.columns = ["datetime", "open", "close", "high", "low", "volume"]
                    stock_info.set_index(pd.DatetimeIndex(stock_info["datetime"]), inplace=True)
                    stock_info.ta.cores = 0
                    stock_info.ta.strategy("All", timed=False)
                    stock_info.insert(0, "股票简称", stock_name)
                    stock_info.insert(0, "股票代码", stock_code)
                    stock_info.columns = [col.replace(".", "x") for col in stock_info.columns]
                    stock_info_list.append(stock_info)
            except AttributeError:
                print(f"{stock_code}_{stock_name}数据有问题！！！")

        upload_df = pd.concat(stock_info_list)
        # 插入数据库
        db_table_name = "hh_quant_stock_technical_analysis_info_daily"
        upload_df.to_sql(db_table_name, self.db_conn, if_exists=if_exists, index=False)

    def upload_stock_label_info_daily(self, start_date, end_date, if_exists="append"):
        """
        基于历史行情数据的Label指标数据
        """
        stock_info_list = []
        for stock_code, stock_name in tqdm(self.get_stock_info_records(), desc="upload_stock_label_info_daily..."):
            try:
                stock_info = ak.stock_zh_a_hist(symbol=stock_code, adjust="hfq", start_date=start_date, end_date=end_date)
                stock_info = stock_info.dropna()
                if not stock_info.empty:
                    stock_info = stock_info.iloc[:, :6]
                    stock_info.columns = ["日期", "open", "close", "high", "low", "volume"]
                    stock_info.set_index(pd.DatetimeIndex(stock_info["日期"]), inplace=True)
                    # 构建Label(第二天涨幅超过5%则为1，否则为0)
                    stock_info["标签"] = (((stock_info["close"] - stock_info["open"]) / stock_info["open"]) >= 0.05).astype(int)
                    stock_info.insert(0, "股票简称", stock_name)
                    stock_info.insert(0, "股票代码", stock_code)
                    # 构建label表
                    stock_info_list.append(stock_info[["股票代码", "日期", "标签"]])
            except AttributeError:
                print(f"{stock_code}_{stock_name}数据有问题！！！")
        upload_df = pd.concat(stock_info_list)
        db_table_name = "hh_quant_stock_label_info_daily"
        upload_df.to_sql(db_table_name, self.db_conn, if_exists=if_exists, index=False)

    # 基本面信息
    # 资产负债表+利润表+现金流量表
    # 咨询数据
    # 等等等等


if __name__ == "__main__":
    database_conn = sqlite3.connect("hh_quant.db")
    start_date = "19000101"
    end_date = "20240101"

    uploader = UploadFromAkToDb(database_conn=database_conn)
    # uploader.upload_stock_individual_info(if_exists='replace') # 已完成
    # uploader.upload_stock_history_info(start_date, end_date, if_exists='append') # 已完成
    # uploader.upload_stock_label_info_daily(start_date, end_date, if_exists='append') # 已完成
    uploader.upload_stock_technical_analysis_info_daily(start_date, end_date, if_exists="replace")

    # 关闭数据库连接
    database_conn.close()
