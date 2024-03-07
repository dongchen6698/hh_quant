# backtest/backtest_engine.py
import warnings

warnings.filterwarnings("ignore")

import sys

# 配置搜索路径
sys.path.append("./")
sys.path.append("../")
sys.path.append("../../")
import backtrader as bt
import pandas as pd
import pprint
import akshare as ak
import sqlite3
from tqdm import tqdm
from datetime import datetime
from strategies import CustomMLStrategy
from backtest_utils import CustomCommissionSchema, CustomAnalyzer
from Share.database.downloader.downloader_base import DownloaderBase
import Share.database.database_config as db_config

# from backtrader_plotting import Bokeh
# from backtrader_plotting.schemes import Tradimo


BACKTEST_INITIAL_CASH = 100000  # 初始化资金
BACKTEST_SIZER = 100  # 设定每笔交易100股
BACKTEST_SLIPPAGE_TYPE = "perc"  # 初始化双边滑点类型
BACKTEST_SLIPPAGE_VALUE = 0.0001  # 初始化双边滑点0.0001
BACKTEST_START_DATE = "20200101"  # 回测开始日期
BACKTEST_END_DATE = "20201231"  # 回测结束日期
BACKTEST_INDEX_SYMBOLS = "000300"  # 【选股】策略的对比基准=指数index，【择时】策略的对比基准=单股自身
BACKTEST_STOCK_SYMBOLS = (
    pd.read_pickle("./backtest_data/stock_selection_result.pkl")["stock_code"].map(lambda x: str(x).zfill(6)).unique().tolist()
)  # 获取模型预测结果的所有stock_code


class BacktestEngine:
    def __init__(self, db_downloader):
        self.cerebro = bt.Cerebro()  # 初始化 Cerebro 引擎
        self.db_downloader = db_downloader

    def run_init_config(self):
        print("开始设置回测基础参数...")
        self.cerebro.broker.setcash(BACKTEST_INITIAL_CASH)  # 配置初始资金量
        self.cerebro.broker.addcommissioninfo(CustomCommissionSchema())  # 配置自定义的佣金类型
        # if BACKTEST_SLIPPAGE_TYPE == "fix":  # 每笔交易滑点为固定值
        #     self.cerebro.broker.set_slippage_fixed(BACKTEST_SLIPPAGE_VALUE)
        # elif BACKTEST_SLIPPAGE_TYPE == "perc":  # 每笔交易滑点为百分比
        #     self.cerebro.broker.set_slippage_perc(BACKTEST_SLIPPAGE_VALUE)
        self.cerebro.addsizer(bt.sizers.FixedSize, stake=BACKTEST_SIZER)  # 配置固定的交易数量

    def run_init_stock_data(self):
        print("开始添加回测股票数据...")
        for stock_symbol in tqdm(BACKTEST_STOCK_SYMBOLS):
            stock_data = self.db_downloader._download_stock_history_info(stock_symbol, start_date=BACKTEST_START_DATE, end_date=BACKTEST_END_DATE)
            if not stock_data.empty:
                stock_data = stock_data[["datetime", "open", "high", "low", "close", "volume"]]
                stock_data["datetime"] = pd.to_datetime(stock_data["datetime"])
                stock_data.set_index("datetime", inplace=True)
                stock_data_feeds = bt.feeds.PandasData(dataname=stock_data)  # 构建回测数据Feeds流
                self.cerebro.adddata(stock_data_feeds, name=stock_symbol)  # 添加回测数据

    def run_init_benchmark_data(self):
        print("开始添加基准数据...")
        benchmark_data = self.db_downloader._download_index_history_info(BACKTEST_INDEX_SYMBOLS, start_date=BACKTEST_START_DATE, end_date=BACKTEST_END_DATE)
        benchmark_data = benchmark_data[["datetime", "open", "high", "low", "close", "volume"]]
        benchmark_data["datetime"] = pd.to_datetime(benchmark_data["datetime"])
        benchmark_data.set_index("datetime", inplace=True)
        self.benchmark_name = f"benchmark_{BACKTEST_INDEX_SYMBOLS}"
        self.benchmark_data_feeds = bt.feeds.PandasData(dataname=benchmark_data)  # 构建基准数据Feeds流
        self.cerebro.adddata(self.benchmark_data_feeds, name=self.benchmark_name)  # 添加基准数据

    def run_init_strategy(self, strategy, **kwargs):
        print("开始添加策略...")
        kwargs["benchmark"] = self.benchmark_name
        self.cerebro.addstrategy(strategy, **kwargs)

    def run_init_analyzer(self):
        print("开始添加分析器...")
        self.cerebro.addanalyzer(bt.analyzers.DrawDown, _name="drawdown")  # 添加最大回撤的分析器，后续customAnalyzer中需要用到
        self.cerebro.addanalyzer(CustomAnalyzer, _name="custom_analyzer")  # 添加自定义的分析器

    def run_init_observer(self):
        print("开始添加观察器...")
        self.cerebro.addobserver(bt.observers.Benchmark, data=self.benchmark_data_feeds, timeframe=bt.TimeFrame.NoTimeFrame)  # 添加基准对比观察器

    def run_backtest(self):
        print("开始运行回测...")
        # 运行回测
        self.results = self.cerebro.run()
        # 打印初始资金
        print(f"Start Portfolio Value: {BACKTEST_INITIAL_CASH}")
        # 打印最终资金
        print(f"Final Portfolio Value: {self.cerebro.broker.getvalue()}")

    def run_evaluate_performance(self, plot=False):
        custom_analysis = self.results[0].analyzers.custom_analyzer.get_analysis()
        print("Start Print Analysis Result .................")
        format_analysis_result = {"基准": {}, "策略": {}, "其他": {}}
        for key, value in custom_analysis.items():
            if key.startswith("基准"):
                format_analysis_result["基准"][key] = round(value, 4)
            elif key.startswith("策略"):
                format_analysis_result["策略"][key] = round(value, 4)
            else:
                format_analysis_result["其他"][key] = round(value, 4)
        pprint.pprint(format_analysis_result)
        # 可以在这里进行更详细的性能评估和可视化
        if plot:
            self.cerebro.plot()

            # b = Bokeh(style="bar", plot_mode="single", scheme=Tradimo())
            # self.cerebro.plot(b)


if __name__ == "__main__":
    # 初始化db_downloader
    db_conn = sqlite3.connect("../../Share/database/hh_quant.db")
    db_downloader = DownloaderBase(db_conn=db_conn, db_config=db_config)
    # 初始化回测引擎
    backtest_engine = BacktestEngine(db_downloader=db_downloader)
    # 配置基础参数
    backtest_engine.run_init_config()
    # 配置数据
    backtest_engine.run_init_stock_data()  # 配置回测数据
    backtest_engine.run_init_benchmark_data()  # 配置基准数据
    # 配置策略
    strategy_params = {
        "model_prediction_file": "./backtest_data/stock_selection_result.pkl",
    }
    backtest_engine.run_init_strategy(CustomMLStrategy, **strategy_params)
    # 配置分析器
    backtest_engine.run_init_analyzer()
    # 配置benchmark
    backtest_engine.run_init_observer()
    # 启动回测
    backtest_engine.run_backtest()
    # 打印性能指标
    backtest_engine.run_evaluate_performance(plot=False)
