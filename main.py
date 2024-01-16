import matplotlib

matplotlib.use("Agg")  # 在导入Backtrader之前设置后端

import logging
import json
import backtrader as bt
from strategies.simple_strategies.moving_average_strategy import MovingAverageStrategy
from utils.data_loader import load_data, load_candidates
from utils.data_saver import save_backtest_result

from backtrader_plotting import Bokeh
from backtrader_plotting.schemes import Tradimo


def run_back_test():
    # 设置回测基础参数
    print("设置回测基础参数...")
    BACKTEST_INITIAL_CASH = 100000  # 初始化资金
    BACKTEST_COMMISSION = 0.0003  # 初始化双边佣金0.0003
    BACKTEST_SIZER = 100  # 设定每笔交易100股
    BACKTEST_SLIPPAGE_TYPE = "perc"  # 初始化双边滑点类型
    BACKTEST_SLIPPAGE_VALUE = 0.0001  # 初始化双边滑点0.0001
    BACKTEST_START_DATE = "20200101"  # 回测开始日期
    BACKTEST_END_DATE = "20240101"  # 回测结束日期
    BACKTEST_STOCK_SYMBOLS = ["300197", "300810", "300125"]  # 回测股票代码
    BACKTEST_OPTIMIZE_STRATEGY = False  # 是否启用优化策略

    # 初始化Cerebro
    print("开始初始化Cerebro...")
    cerebro = bt.Cerebro()
    cerebro.broker.setcash(BACKTEST_INITIAL_CASH)
    cerebro.broker.setcommission(commission=BACKTEST_COMMISSION)
    if BACKTEST_SLIPPAGE_TYPE == "fix":  # 每笔交易滑点为固定值
        cerebro.broker.set_slippage_fixed(BACKTEST_SLIPPAGE_VALUE)
    elif BACKTEST_SLIPPAGE_TYPE == "perc":  # 每笔交易滑点为百分比
        cerebro.broker.set_slippage_perc(BACKTEST_SLIPPAGE_VALUE)
    cerebro.addsizer(bt.sizers.FixedSize, stake=BACKTEST_SIZER)

    # 添加分析器
    print("开始添加分析器...")
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name="ta")  # 交易分析器
    cerebro.addanalyzer(bt.analyzers.SQN, _name="sqn")  # SQN分析器
    cerebro.addanalyzer(bt.analyzers.TimeReturn, _name="pnl")  # 盈亏分析器
    cerebro.addanalyzer(bt.analyzers.AnnualReturn, _name="annual_return")  # 年化收益分析器
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name="sharpe_ratio")  # 普比率分析器
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name="drawdown")  # 最大回撤分析器

    # 添加MovingAverageStrategy
    print("开始添加策略...")
    cerebro.addstrategy(MovingAverageStrategy, fast_length=10, slow_length=30)
    if BACKTEST_OPTIMIZE_STRATEGY:
        cerebro.optstrategy(MovingAverageStrategy, fast_length=range(3, 10), slow_length=range(30, 60))

    # 导入对应的股票数据到cerebro
    print("开始导入数据...")
    stock_candidates = load_candidates(BACKTEST_STOCK_SYMBOLS)
    for stock_symbol, stock_name in stock_candidates:
        stock_data = load_data(stock_symbol, start_date=BACKTEST_START_DATE, end_date=BACKTEST_END_DATE)
        if stock_data is not None:
            cerebro.adddata(stock_data, name=f"{stock_symbol}_{stock_name}")

    # 运行回测
    print("开始运行回测...")
    backtest_result = cerebro.run()

    # 结束回测
    print("结束回测...")
    print(f"Start Portfolio Value: {BACKTEST_INITIAL_CASH:.2f}")
    print(f"Final Portfolio Value: {cerebro.broker.getvalue():.2f}")

    # 计算回测的性能指标，如夏普比率、最大回撤等
    print("计算回测的性能指标，如夏普比率、最大回撤等...")
    backtest_profile = {
        "backtest_basic_info": {
            "starting_portfolio_value": BACKTEST_INITIAL_CASH,
            "commission": BACKTEST_COMMISSION,
            "sizer": BACKTEST_SIZER,
            "slippage_type": BACKTEST_SLIPPAGE_TYPE,
            "slippage_value": BACKTEST_SLIPPAGE_VALUE,
            "final_portfolio_value": cerebro.broker.getvalue(),
        },
        "backtest_data_info": {"start_date": BACKTEST_START_DATE, "end_date": BACKTEST_END_DATE},
        "backtest_performance_info": {
            "sharpe_ratio": backtest_result[0].analyzers.sharpe_ratio.get_analysis().get("sharperatio"),
            "max_drawdown": backtest_result[0].analyzers.drawdown.get_analysis().max.drawdown,
            "annual_return": backtest_result[0].analyzers.annual_return.get_analysis(),
        },
    }
    print(f"backtest_profile: {json.dumps(backtest_profile, ensure_ascii=False, indent=4)}")

    # 可视化展现
    print("可视化展现...")
    b = Bokeh(style="bar", plot_mode="single", scheme=Tradimo())
    cerebro.plot(b)

    # 将本次回测的结果保存至结果目录
    # result_dir = "./results"
    # save_backtest_result(result_dir, backtest_profile, cerebro)


if __name__ == "__main__":
    # 运行回测
    print("Starting BackTesting...")
    run_back_test()

    # 实盘模拟
    # print("Starting LiveMocking...")
    # run_live_mock()

    # 实盘交易
    # print("Starting LiveTrading...")
    # run_live_trading()
