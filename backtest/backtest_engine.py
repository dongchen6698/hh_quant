# backtest/backtest_engine.py

import backtrader as bt
from utils.data_loader import load_backtest_data
import backtest_config as backtest_config
from ..strategies.simple_strategies.moving_average_strategy import MovingAverageCrossStrategy


class BacktestEngine:
    def __init__(self):
        self.cerebro = bt.Cerebro()  # 初始化 Cerebro 引擎

    def run_init_config(self, backtest_config):
        print("设置回测基础参数...")
        self.cerebro.broker.setcash(backtest_config.BACKTEST_INITIAL_CASH)
        self.cerebro.broker.setcommission(commission=backtest_config.BACKTEST_COMMISSION)
        if backtest_config.BACKTEST_SLIPPAGE_TYPE == "fix":  # 每笔交易滑点为固定值
            self.cerebro.broker.set_slippage_fixed(backtest_config.BACKTEST_SLIPPAGE_VALUE)
        elif backtest_config.BACKTEST_SLIPPAGE_TYPE == "perc":  # 每笔交易滑点为百分比
            self.cerebro.broker.set_slippage_perc(backtest_config.BACKTEST_SLIPPAGE_VALUE)
        self.cerebro.addsizer(bt.sizers.FixedSize, stake=backtest_config.BACKTEST_SIZER)

    def run_init_analyzer(self):
        print("开始添加分析器...")
        self.cerebro.addanalyzer(bt.analyzers.TimeReturn, _name="pnl")  # 盈亏分析器
        self.cerebro.addanalyzer(bt.analyzers.AnnualReturn, _name="annual_return")  # 年化收益分析器
        self.cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name="sharpe_ratio")  # 普比率分析器
        self.cerebro.addanalyzer(bt.analyzers.DrawDown, _name="drawdown")  # 最大回撤分析器
        self.cerebro.addanalyzer(bt.analyzers.Returns, _name="returns")  # 收益分析器

    def run_init_strategy(self, strategy):
        print("开始添加策略...")
        self.cerebro.addstrategy(strategy)

    def run_init_data(self, symbols=[]):
        # 将数据添加到 Cerebro

        for stock_name, stock_data in data_dict.items():
            self.cerebro.adddata(stock_data, name=stock_name)

    def run_backtest(self):
        # 运行回测
        self.results = self.cerebro.run()
        # 打印初始资金
        print(f"Start Portfolio Value: {self.cerebro.broker.getvalue()}")
        # 打印最终资金
        print(f"Final Portfolio Value: {self.cerebro.broker.getvalue()}")

    def evaluate_performance(self):
        # 提取分析器结果
        sharpe_ratio = self.results[0].analyzers.sharpe_ratio.get_analysis()
        drawdown_info = self.results[0].analyzers.drawdown.get_analysis()
        returns_info = self.results[0].analyzers.returns.get_analysis()

        # 打印性能指标
        print(f'Sharpe Ratio: {sharpe_ratio["sharperatio"]}')
        print(f'Max Drawdown: {drawdown_info["max"]["drawdown"]}')
        print(f'Annual Return: {returns_info["rnorm100"]}')

        # 可以在这里进行更详细的性能评估和可视化


if __name__ == "__main__":
    backtest_engine = BacktestEngine()
    backtest_engine.run_init_config(backtest_config)  # 配置基础参数
    backtest_engine.run_init_analyzer()  # 配置分析器
    backtest_engine.run_init_strategy(MovingAverageCrossStrategy)  # 配置策略
    backtest_engine.run_init_data(symbols=[])  # 配置数据
    backtest_engine.run_backtest()
