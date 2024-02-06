import os
import akshare as ak
from tqdm import tqdm


def download_index_data(index_symbols):
    for index_symbol in tqdm(index_symbols, desc="_downloading index data ..."):
        # 获取指数数据
        index_data = ak.index_zh_a_hist(symbol=index_symbol).rename(
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
        # 保存指数数据
        index_data.to_pickle(f"{INDEX_DATA_DIR}/{index_symbol}.pkl")


def download_stock_data(stock_symbols, adjust_type=""):
    for stock_symbol in tqdm(stock_symbols, desc="_downloading stock data ..."):
        # 获取股票数据
        stock_data = ak.stock_zh_a_hist(symbol=stock_symbol, adjust=adjust_type).rename(
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
        # 保存股票数据
        stock_data.to_pickle(f"{STOCK_DATA_DIR}/{stock_symbol}.pkl")


if __name__ == "__main__":
    # 在这里下载回测需要用到的数据...

    def check_data_dir(dir_path):
        if not os.path.isdir(dir_path):
            os.makedirs(dir_path)

    INDEX_DATA_DIR = "./index_data"
    STOCK_DATA_DIR = "./stock_data"
    check_data_dir(INDEX_DATA_DIR)
    check_data_dir(STOCK_DATA_DIR)

    """
    下载指数数据：
        * 中证指数的6大宽基指数: 中证100(SH:000903)、沪深300(SH:000300)、中证500(SH:000905)、中证800(SH:000906)、中证1000(SH:000852)
    """
    download_index_data(["000903", "000300", "000905", "000906", "000852"])

    """
    下载股票数据：
        * 贵州茅台(600519)
    """
    ADJUST_TYPE = "hfq"  # ""：不复权, "qfq": 前复权, "hfq": 后复权
    download_stock_data(["600519"], ADJUST_TYPE)


"""
目前Backtrader还无法处理股票拆分合并、分红配股带来的影响, 但常规的处理方式是在导入行情数据时, 就直接导入复权后的行情数据（一般选择后复权）, 保证收益的准确性。
"""
