# strategies/moving_average_strategy.py
import backtrader as bt
from .simple_base_strategy import BaseStrategy


class MovingAverageStrategy(BaseStrategy):
    params = {
        "fast_length": 10,  # 快速移动平均线的窗口长度
        "slow_length": 30,  # 慢速移动平均线的窗口长度
    }

    def __init__(self):
        super().__init__()
        self.sma_fast = {}
        self.sma_slow = {}
        self.crossover = {}

        for data in self.datas:
            # 添加快速和慢速移动平均线指标 & 跟踪指标交叉的观察者
            self.sma_fast[data] = bt.indicators.SimpleMovingAverage(data, period=self.params.fast_length)
            self.sma_slow[data] = bt.indicators.SimpleMovingAverage(data, period=self.params.slow_length)
            self.crossover[data] = bt.indicators.CrossOver(self.sma_fast[data], self.sma_slow[data])

    def buy_signal(self, data):
        # 编写买入信号的逻辑，返回True表示应该买入，否则返回False。
        if self.crossover[data] > 0:
            return True
        return False

    def sell_signal(self, data):
        # 编写卖出信号的逻辑，返回True表示应该卖出，否则返回False。
        if self.crossover[data] < 0:
            return True
        return False
