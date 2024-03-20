import sys

sys.path.append("../")

import backtrader as bt
from .base_strategy import BaseStrategy


class MovingAverageCrossStrategy(BaseStrategy):
    params = (
        ("fast_ma_period", 10),  # 快速移动平均线周期
        ("slow_ma_period", 30),  # 慢速移动平均线周期
    )

    def __init__(self):
        # 初始化父类方法 & 参数
        super().__init__()  # 调用基础策略的初始化方法

        # 为每只股票创建指标和订单跟踪的字典
        self.fast_ma = dict()
        self.slow_ma = dict()
        self.crossover = dict()

        # 初始化指标和订单字典
        for data in self.datas:
            self.fast_ma[data] = bt.indicators.SimpleMovingAverage(data, period=self.params.fast_ma_period)
            self.slow_ma[data] = bt.indicators.SimpleMovingAverage(data, period=self.params.slow_ma_period)
            self.crossover[data] = bt.indicators.CrossOver(self.fast_ma[data], self.slow_ma[data])

    def next(self):
        for data in self.datas:
            # 检查是否有挂起的订单
            if self.orders[data]:
                continue

            # 检查是否持有当前股票
            data_position = self.getposition(data).size
            if not data_position:
                # 如果快速MA穿越慢速MA向上，买入信号
                if self.crossover[data] > 0:
                    self.buy(data=data, size=100, exectype=bt.Order.Market)
            else:
                # 如果快速MA穿越慢速MA向下，卖出信号
                if self.crossover[data] < 0:
                    self.close(data=data, exectype=bt.Order.Market)


class MACDStrategy(BaseStrategy):
    params = (
        ("macd1", 12),  # 快速EMA周期
        ("macd2", 26),  # 慢速EMA周期
        ("signal", 9),  # 信号线EMA周期
    )

    def __init__(self):
        super().__init__()  # 调用基础策略的初始化方法

        # 为每只股票创建MACD和交叉信号的字典
        self.macd = dict()
        self.signal = dict()
        self.crossover = dict()

        # 初始化MACD指标和交叉信号字典
        for data in self.datas:
            self.macd[data] = bt.indicators.MACD(
                data,
                period_me1=self.params.macd1,
                period_me2=self.params.macd2,
                period_signal=self.params.signal,
            )
            self.crossover[data] = bt.indicators.CrossOver(
                self.macd[data].macd,
                self.macd[data].signal,
            )

    def next(self):
        for data in self.datas:
            # 检查是否有挂起的订单
            if self.orders[data]:
                continue

            # 检查是否持有当前股票
            data_position = self.getposition(data).size
            if not data_position:
                # 如果MACD线穿越信号线向上，买入信号
                if self.crossover[data] > 0:
                    self.orders[data] = self.buy(data=data)
            else:
                # 如果MACD线穿越信号线向下，卖出信号
                if self.crossover[data] < 0:
                    self.orders[data] = self.sell(data=data)
