import backtrader as bt
from strategies.base_strategy import BaseStrategy


class MovingAverageCrossStrategy(BaseStrategy):
    params = (
        ("fast_ma_period", 10),  # 快速移动平均线周期
        ("slow_ma_period", 30),  # 慢速移动平均线周期
    )

    def __init__(self):
        super().__init__()  # 调用基础策略的初始化方法

        # 为每只股票创建指标和订单跟踪的字典
        self.fast_ma = dict()
        self.slow_ma = dict()
        self.crossover = dict()
        self.orders = dict()

        # 初始化指标和订单字典
        for data in self.datas:
            self.fast_ma[data] = bt.indicators.SimpleMovingAverage(data, period=self.p.fast_ma_period)
            self.slow_ma[data] = bt.indicators.SimpleMovingAverage(data, period=self.p.slow_ma_period)
            self.crossover[data] = bt.indicators.CrossOver(self.fast_ma[data], self.slow_ma[data])

    def next(self):
        for data in self.datas:
            # 检查是否有挂起的订单
            if self.ordersdata:
                continue

            # 检查是否持有当前股票的头寸
            if not self.getposition(data).size:
                # 如果快速MA穿越慢速MA向上，买入信号
                if self.crossover[data] > 0:
                    self.log(f"BUY CREATE {data._name}, {data.close[0]}")
                    self.orders[data] = self.buy(data=data)
            else:
                # 如果快速MA穿越慢速MA向下，卖出信号
                if self.crossover[data] < 0:
                    self.log(f"SELL CREATE {data._name}, {data.close[0]}")
                    self.orders[data] = self.sell(data=data)
