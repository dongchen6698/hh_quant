# backtest/backtest_engine.py

import backtrader as bt
from utils.data_loader import load_backtest_data


class BacktestEngine:
    def __init__(self, strategy, config):
        self.strategy = strategy
        self.config = config
        self.cerebro = bt.Cerebro()  # 初始化 Cerebro 引擎

    def run_init_config(self):
        print("设置回测基础参数...")
        self.cerebro.broker.setcash(self.config.BACKTEST_INITIAL_CASH)
        self.cerebro.broker.setcommission(commission=self.config.BACKTEST_COMMISSION)
        if self.config.BACKTEST_SLIPPAGE_TYPE == "fix":  # 每笔交易滑点为固定值
            self.cerebro.broker.set_slippage_fixed(self.config.BACKTEST_SLIPPAGE_VALUE)
        elif self.config.BACKTEST_SLIPPAGE_TYPE == "perc":  # 每笔交易滑点为百分比
            self.cerebro.broker.set_slippage_perc(self.config.BACKTEST_SLIPPAGE_VALUE)
        self.cerebro.addsizer(bt.sizers.FixedSize, stake=self.config.BACKTEST_SIZER)

    def run_init_analyzer(self):
        print("开始添加分析器...")
        self.cerebro.addanalyzer(bt.analyzers.TimeReturn, _name="pnl")  # 盈亏分析器
        self.cerebro.addanalyzer(bt.analyzers.AnnualReturn, _name="annual_return")  # 年化收益分析器
        self.cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name="sharpe_ratio")  # 普比率分析器
        self.cerebro.addanalyzer(bt.analyzers.DrawDown, _name="drawdown")  # 最大回撤分析器
        self.cerebro.addanalyzer(bt.analyzers.Returns, _name="returns")  # 收益分析器

    def run_init_strategy(self):
        print("开始添加策略...")
        self.cerebro.addstrategy(self.strategy)

    def run_init_data(self):
        # 将数据添加到 Cerebro
        data_dict = load_backtest_data(
            self.config.BACKTEST_STOCK_SYMBOLS,
            self.config.BACKTEST_START_DATE,
            self.config.BACKTEST_END_DATE,
        )
        for stock_name, stock_data in data_dict.items():
            self.cerebro.adddata(stock_data, name=stock_name)

    def run_backtest(self):
        self.run_init_config()  # 配置基础参数
        self.run_init_analyzer()  # 配置分析器
        self.run_init_strategy()  # 配置策略
        self.run_init_data()  # 配置数据
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
