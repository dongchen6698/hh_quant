import sqlite3
import pandas as pd
from datetime import datetime, timedelta


class Preprocessing:
    def __init__(self, db_conn, start_date, end_date, max_lookback_window=180) -> None:
        self.db_conn = db_conn
        self.start_date = datetime.strftime(datetime.strptime(start_date, "%Y%m%d"), "%Y-%m-%d")
        self.end_date = datetime.strftime(datetime.strptime(end_date, "%Y%m%d"), "%Y-%m-%d")
        # 根据max_lookback_window计算出lookback_start_date
        self.lookback_start_date = datetime.strftime(datetime.strptime(start_date, "%Y%m%d") - timedelta(days=max_lookback_window), "%Y-%m-%d")
        print(f"new_start_date:: {self.lookback_start_date}")

    def _extract_stock_history_data(self):
        table_name = "hh_quant_stock_history_info"
        self.stock_history_df = pd.read_sql(
            f"SELECT * FROM {table_name} WHERE datetime BETWEEN '{self.lookback_start_date}' AND '{self.end_date}'", self.db_conn
        )

    # 抽取其他类型的特征数据

    def _build_stock_label_data(self):
        """
        Label:
        0: 未来5天收益率在历史窗口期内的平均收益率+-2*标准差内
        1: 未来5天收益率超过历史窗口期内的平均收益率+2*标准差
        -1: 未来5天收益率低于历史窗口期内的平均收益率-2*标准差
        """
        # 构建训练数据的Label表
        self.stock_label_df = self.stock_history_df.sort_values(by=["stock_code", "datetime"])
        # 计算日收益率 & 历史窗口期内的平均收益率-标准差
        self.stock_label_df["daily_return"] = self.stock_label_df.groupby("stock_code")["close"].pct_change()
        self.stock_label_df["mean_return"] = self.stock_label_df.groupby("stock_code")["daily_return"].transform(lambda x: x.rolling(10).mean())
        self.stock_label_df["std_return"] = self.stock_label_df.groupby("stock_code")["daily_return"].transform(lambda x: x.rolling(10).std())
        # 计算未来5天的收益率
        self.stock_label_df["close_in_5_days"] = self.stock_label_df.groupby("stock_code")["close"].shift(-5)
        self.stock_label_df["return_5_days"] = self.stock_label_df["close_in_5_days"] / self.stock_label_df["close"] - 1
        # 构建label列
        self.stock_label_df["label"] = 0  # 默认设置为0
        self.stock_label_df.loc[self.stock_label_df["return_5_days"] > self.stock_label_df["mean_return"] + 2 * self.stock_label_df["std_return"], "label"] = 1
        self.stock_label_df.loc[self.stock_label_df["return_5_days"] < self.stock_label_df["mean_return"] - 2 * self.stock_label_df["std_return"], "label"] = -1
        # 删除有NaN值的行，因为历史统计和未来数据可能不完整
        self.stock_label_df.dropna(subset=["mean_return", "std_return", "close_in_5_days"], inplace=True)
        # 构建Label表
        self.stock_label_df = self.stock_label_df[["stock_code", "datetime", "label"]]

    def _merge_label_and_feature(self):
        self.preprocessing_result = self.stock_label_df.merge(self.stock_history_df, on=["stock_code", "datetime"], how="left")
        # 还需要merge其他类型的特征数据
        # 插入数据库
        self.preprocessing_result.to_sql("hh_quant_stock_preprocessing_result_info", self.db_conn, if_exists="replace", index=False)

    def start(self):
        print("开始预处理数据...")
        self._extract_stock_history_data()
        self._build_stock_label_data()
        self._merge_label_and_feature()


if __name__ == "__main__":
    db_conn = sqlite3.connect("database/hh_quant.db")
    preprocessing = Preprocessing(db_conn=db_conn, start_date="20050101", end_date="20100101", max_lookback_window=180)
    preprocessing.start()
