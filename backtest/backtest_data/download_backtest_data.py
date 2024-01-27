import os
import akshare as ak
from tqdm import tqdm


def main():
    backtest_start_date = "20230101"
    backtest_end_date = "20240101"
    backtest_adjust_type = "hfq"  # ''：不复权，'qfq':前复权，'hfq': 后复权
    backtest_data_dir = "./stock_data"

    if not os.path.isdir(backtest_data_dir):
        os.makedirs(backtest_data_dir)

    for stock_code, stock_name in tqdm(ak.stock_info_a_code_name().to_records(index=False), desc="_download_backtest_data..."):
        stock_info = ak.stock_zh_a_hist(symbol=stock_code, adjust=backtest_adjust_type, start_date=backtest_start_date, end_date=backtest_end_date)
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
            stock_info.insert(0, "stock_adjust", backtest_adjust_type)
            stock_info.insert(0, "stock_name", stock_name)
            stock_info.insert(0, "stock_code", stock_code)
            # 插入数据库
            stock_info.to_pickle(f"{backtest_data_dir}/{stock_code}_{stock_name}.pkl")
        else:
            print(f"Current Stock Data {stock_code}_{stock_name} is Empty....")


if __name__ == "__main__":
    main()
