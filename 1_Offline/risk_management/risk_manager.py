import backtrader as bt


class RiskManager:
    def __init__(self, strategy):
        self.strategy = strategy

    def check_stop_loss(self, data, stop_loss_percent=10):
        # 获取当前多头持仓
        position = self.strategy.getposition(data)
        if position.size > 0:  # 检查是否有多仓
            # 计算止损价格
            stop_price = position.price * (1 - stop_loss_percent / 100)
            # 获取当前价格
            current_price = data.close[0]
            # 如果当前价格低于止损价格，执行平仓
            if current_price < stop_price:
                self.strategy.log(f"触发止损【stop_price: {stop_price}, current_price: {current_price}】，执行平仓，股票:{data._name}")
                self.strategy.close(data)

    def check_take_profit(self, data, take_profit_percent=30):
        # 获取当前多头持仓
        position = self.strategy.getposition(data)
        if position.size > 0:  # 检查是否有多仓
            # 计算止盈价格
            take_profit_price = position.price * (1 + take_profit_percent / 100)
            # 获取当前价格
            current_price = data.close[0]
            # 如果当前价格高于止盈价格，执行平仓
            if current_price > take_profit_price:
                self.strategy.log(f"触发止盈，执行平仓，股票:{data._name}")
                self.strategy.close(data)

    def check_max_holding_period(self, data, max_holding_period=10):
        # 获取当前数据源的所有交易
        trades = self.strategy._trades[data]
        # 遍历所有交易，找到第一个开放的交易
        for trade in trades:
            if trade.isopen:
                # 计算持仓持续的周期数
                holding_period = len(self.strategy) - trade.baropen
                # 如果持仓时间超过最大持仓周期，则平仓
                if holding_period >= max_holding_period:
                    self.strategy.log(f"触发最大持仓周期{max_holding_period}天，执行平仓，股票:{data._name}")
                    self.strategy.close(data)
                    break  # 只需要处理第一个开放的交易

    def check_volatility_adjustment(self, vol_target=None, vol_lookback=None):
        # 这个方法可能需要根据您的具体需求进行调整
        pass
