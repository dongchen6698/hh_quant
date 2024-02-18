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
                    self.orders[data] = self.buy(data=data)
            else:
                # 如果快速MA穿越慢速MA向下，卖出信号
                if self.crossover[data] < 0:
                    self.orders[data] = self.sell(data=data)


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


class MixStrategy(BaseStrategy):
    params = (
        ("sma_fast_period", 10),
        ("sma_slow_period", 30),
        ("macd1", 12),
        ("macd2", 26),
        ("macdsig", 9),
        ("kdj_k_period", 14),
        ("kdj_d_period", 3),
        ("donchian_period", 20),
    )

    def __init__(self):
        super().__init__()  # 调用基础策略的初始化方法
        self.sma_fast = dict()
        self.sma_slow = dict()
        self.sma_xover = dict()
        self.macd = dict()
        self.macd_xover = dict()
        self.kdj = dict()
        self.kdj_xover = dict()
        self.donchian_upper = dict()
        self.donchian_lower = dict()

        for data in self.datas:
            # 初始化移动均线
            self.sma_fast[data] = bt.indicators.SimpleMovingAverage(data, period=self.params.sma_fast_period)
            self.sma_slow[data] = bt.indicators.SimpleMovingAverage(data, period=self.params.sma_slow_period)
            self.sma_xover[data] = bt.indicators.CrossOver(self.sma_fast[data], self.sma_slow[data])

            # 初始化MACD指标
            self.macd[data] = bt.indicators.MACD(data, period_me1=self.params.macd1, period_me2=self.params.macd2, period_signal=self.params.macdsig)
            self.macd_xover[data] = bt.indicators.CrossOver(self.macd[data].macd, self.macd[data].signal)

            # 初始化KDJ指标
            self.kdj[data] = bt.indicators.StochasticSlow(
                data,
                period=self.params.kdj_k_period,  # 原始 %K 线的计算周期
                period_dfast=self.params.kdj_d_period,  # 快速 %D 线的计算周期，即对 %K 线进行平滑处理的周期，通常设为3
                period_dslow=self.params.kdj_d_period,  # 慢速 %D 线的计算周期，即对快速 %D 线进行再次平滑处理的周期，通常也设为3
            )
            self.kdj_xover[data] = bt.indicators.CrossOver(self.kdj[data].percK, self.kdj[data].percD)

            # 初始化唐奇安通道指标
            self.donchian_upper[data] = bt.indicators.Highest(data.high(-1), period=self.params.donchian_period)
            self.donchian_lower[data] = bt.indicators.Lowest(data.low(-1), period=self.params.donchian_period)

    def next(self):
        for data in self.datas:
            # 检查是否有挂起的订单
            if self.orders[data]:
                continue

            # 检查是否持有当前股票
            data_position = self.getposition(data).size

            # 策略投票
            buy_signal = 0
            buy_signal += int(self.sma_xover[data] > 0)  # SMA交叉向上
            buy_signal += int(self.macd_xover[data] > 0)  # MACD交叉向上
            buy_signal += int(self.kdj_xover[data] > 0)  # KDJ交叉向上
            buy_signal += int(data.close[0] > self.donchian_upper[data][0])  # 收盘价大于唐奇安通道上轨

            sell_signal = 0
            sell_signal += int(self.sma_xover[data] < 0)  # SMA交叉向下
            sell_signal += int(self.macd_xover[data] < 0)  # MACD交叉向下
            sell_signal += int(self.kdj_xover[data] < 0)  # KDJ交叉向下
            sell_signal += int(data.close[0] < self.donchian_lower[data][0])  # 收盘价小于唐奇安通道下轨

            if not data_position and buy_signal > sell_signal:
                self.orders[data] = self.buy(data=data)
            elif data_position and buy_signal < sell_signal:
                self.orders[data] = self.sell(data=data)
