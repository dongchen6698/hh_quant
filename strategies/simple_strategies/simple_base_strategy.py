# strategies/base_strategy.py

import backtrader as bt


class BaseStrategy(bt.Strategy):
    params = {
        "log_file": None,
        "take_profit": 0.05,  # 止盈百分比
        "stop_loss": 0.03,  # 止损百分比
    }

    def __init__(self):
        self.order = None  # 用于跟踪订单
        self.buyprice = None
        self.buycomm = None
        # 你可以在这里添加共通的指标初始化

    def log(self, txt, dt=None, doprint=True):
        """日志记录函数"""
        if self.params.log_file or doprint:
            dt = dt or self.datas[0].datetime.date(0)
            print(f"{dt.isoformat()} {txt}")  # 打印时间和日志信息

    def notify_order(self, order):
        """订单状态通知"""
        if order.status in [order.Submitted, order.Accepted]:
            # 订单已提交或已接受处理
            return

        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(
                    "BUY EXECUTED, ref:%.0f，Price: %.2f, Cost: %.2f, Comm %.2f, Size: %.2f, Stock: %s"
                    % (
                        order.ref,  # 订单编号
                        order.executed.price,  # 成交价
                        order.executed.value,  # 成交额
                        order.executed.comm,  # 佣金
                        order.executed.size,  # 成交量
                        order.data._name,
                    )
                )
            else:  # 卖出
                self.log(
                    "SELL EXECUTED, ref:%.0f, Price: %.2f, Cost: %.2f, Comm %.2f, Size: %.2f, Stock: %s"
                    % (
                        order.ref,
                        order.executed.price,
                        order.executed.value,
                        order.executed.comm,
                        order.executed.size,
                        order.data._name,
                    )
                )
            self.bar_executed = len(self)

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log("Order Canceled/Margin/Rejected")

        # # 写入日志文件（如果需要）
        # if self.params.log_file:
        #     with open(self.params.log_file, 'a') as f:
        #         f.write(f"{self.datas[0].datetime.date(0)}, {txt}\n")

        # 没有挂起的订单
        self.order = None

    def notify_trade(self, trade):
        if not trade.isclosed:
            return
        self.log("OPERATION PROFIT, GROSS %.2f, NET %.2f" % (trade.pnl, trade.pnlcomm))

    def buy_signal(self, data):
        """
        编写买入信号的逻辑，返回True表示应该买入，否则返回False。
        """
        return False  # 默认不买入

    def sell_signal(self, data):
        """
        编写卖出信号的逻辑，返回True表示应该卖出，否则返回False。
        """
        return False  # 默认不卖出

    def position_size_control(self, data):
        """
        控制持仓数量的逻辑，返回一个整数，表示应该持有的数量。
        """
        return 0  # 默认不持仓

    def apply_take_profit_stop_loss(self, data):
        """
        构建止盈止损逻辑
        """
        # 获取当前持仓
        position = self.getposition(data)
        # 没有持仓，不执行止盈止损
        if not position:
            return False  # 没有持仓，未执行止盈止损
        # 获取当前持仓的购买价格
        buy_price = position.price
        # 获取当前持仓的当前价格
        current_price = data.close[0]

        # 计算止盈和止损价格
        take_profit_price = buy_price * (1 + self.params.take_profit)
        stop_loss_price = buy_price * (1 - self.params.stop_loss)

        if current_price >= take_profit_price:
            self.log("TAKE PROFIT, {:.2f}".format(current_price))
            self.close(data=data)
            return True  # 止盈成功

        elif current_price <= stop_loss_price:
            self.log("STOP LOSS, {:.2f}".format(current_price))
            self.close(data=data)
            return True  # 止损成功

        return False  # 未触发止盈止损

    def next(self):
        if self.order:
            return

        for data in self.datas:
            if self.getposition(data).size:
                if not self.apply_take_profit_stop_loss(data=data):
                    # 如果止盈止损逻辑未成功执行，则继续检查是否需要卖出
                    if self.sell_signal(data):
                        self.log("{} - SELL CREATE, {:.2f}".format(data._name, data.close[0]))
                        # 下一个开盘价卖出
                        self.order = self.sell(data=data)
                    continue
            else:  # 未持有当前股票的情况下
                # 添加买入逻辑
                if self.buy_signal(data):
                    self.log("{} - BUY CREATE, {:.2f}".format(data._name, data.close[0]))
                    # 下一个开盘价买入
                    self.order = self.buy(data=data)
                continue
