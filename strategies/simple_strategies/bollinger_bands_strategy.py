# Import necessary libraries
import backtrader as bt
from ..base_strategy import BaseStrategy


class BollingerBandStrategy(BaseStrategy):
    params = {
        "bollinger_period": 20,  # 布林线的计算周期
        "bollinger_dev_factor": 2.0,  # 布林线的标准差因子
    }

    def __init__(self):
        super().__init__()  # 调用父类的构造函数
        self.bollinger = {}  # 存储每只股票的布林线指标

        for data in self.datas:
            self.bollinger[data] = bt.indicators.BollingerBands(data, period=self.params.bollinger_period, devfactor=self.params.bollinger_dev_factor)

    def buy_signal(self, data):
        # 根据布林线生成买入信号
        if data.close[0] < self.bollinger[data].lines.bot[0]:
            return True
        return False

    def sell_signal(self, data):
        # 根据布林线生成卖出信号
        if data.close[0] > self.bollinger[data].lines.top[0]:
            return True
        return False
