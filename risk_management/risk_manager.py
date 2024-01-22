import backtrader as bt


class RiskManager:
    def __init__(self, strategy):
        self.strategy = strategy

    def check_stop_loss(self, stop_loss_percent=2):
        # 为所有打开的交易检查止损条件
        for trade in self.strategy._trades[self.strategy.data]._trades:
            if trade.isopen:
                # 计算止损价格。这是基于交易开仓价格并根据设置的止损百分比计算得出的。
                stop_price = trade.price * (1 - stop_loss_percent / 100)
                # 获取当前最新的收盘价
                current_price = trade.data.close[0]
                # 如果当前价格低于止损价格，则执行关闭仓位的命令
                if current_price < stop_price:
                    self.strategy.close(trade.data)

    def check_take_profit(self, take_profit_percent=5):
        # 为所有打开的交易检查止盈条件
        for trade in self.strategy._trades[self.strategy.data]._trades:
            # 检查交易是否还是开放状态
            if trade.isopen:
                # 计算止盈价格。这是基于交易开仓价格并根据设置的止盈百分比计算得出的。
                stop_price = trade.price * (1 + take_profit_percent / 100)
                # 获取当前最新的收盘价
                current_price = trade.data.close[0]
                # 如果当前价格高于止盈价格，则执行关闭仓位的命令
                if current_price >= stop_price:
                    self.strategy.close(trade.data)

    def check_max_holding_period(self, max_holding_period=10):
        # 为所有打开的交易检查最大持仓时间
        for trade in self.strategy._trades[self.strategy.data]._trades:
            # 检查交易是否还是开放状态
            if trade.isopen:
                # 计算当前持仓的时间
                # trade.baropen 是开仓时的条目索引
                # len(self.strategy) 是当前的条目索引
                holding_period = len(self.strategy) - trade.baropen

                # 如果持仓时间超过设定的最大持仓时间，平仓
                if holding_period > max_holding_period:
                    self.strategy.close(trade.data)

    def check_volatility_adjustment(self, vol_target, vol_lookback):
        # 基于过去vol_lookback时间段的波动率计算当前波动率
        current_vol = bt.indicators.AverageTrueRange(self.strategy.data, period=vol_lookback)
        # 检查波动率指标是否已经初始化，至少需要vol_lookback周期的数据
        if len(current_vol) > vol_lookback:
            # 如果当前的波动率超过了目标波动率，可能需要调整头寸规模
            if current_vol[0] > vol_target:
                # 示例：根据波动率调整头寸比例
                # 这里仅作为示例，实际的调整策略可能更为复杂
                adjustment_factor = vol_target / current_vol[0]
                self.strategy.order_target_percent(target=adjustment_factor)
