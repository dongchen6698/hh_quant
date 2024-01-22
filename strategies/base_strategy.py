import backtrader as bt


class BaseStrategy(bt.Strategy):
    params = {"log_file": None}

    def __init__(self):
        # 使用字典来跟踪每个数据源的订单、购买价格和佣金
        self.orders = {data: None for data in self.datas}
        self.buyprice = {data: None for data in self.datas}
        self.buycomm = {data: None for data in self.datas}
        # 你可以在这里为每个数据源添加共通的指标初始化

    def log(self, txt, dt=None, doprint=True):
        """日志记录函数"""
        if self.params.log_file or doprint:
            dt = dt or self.datas[0].datetime.date(0)  # 默认使用第一个数据源的日期
            print(f"{dt.isoformat()} {txt}")  # 打印时间和日志信息

    def notify_order(self, order):
        """订单状态通知"""
        data = order.data  # 获取与订单关联的数据源
        if order.status in [order.Submitted, order.Accepted]:
            # 订单已提交或已接受处理
            return
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(
                    f"BUY EXECUTED, ref:{order.ref}, Price: {order.executed.price:.2f}, "
                    f"Cost: {order.executed.value:.2f}, Comm {order.executed.comm:.2f}, "
                    f"Size: {order.executed.size:.2f}, Stock: {data._name}"
                )
                self.buyprice[data] = order.executed.price
                self.buycomm[data] = order.executed.comm
            elif order.issell():
                self.log(
                    f"SELL EXECUTED, ref:{order.ref}, Price: {order.executed.price:.2f}, "
                    f"Cost: {order.executed.value:.2f}, Comm {order.executed.comm:.2f}, "
                    f"Size: {order.executed.size:.2f}, Stock: {data._name}"
                )
            self.orders[data] = None
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log("Order Canceled/Margin/Rejected")
            self.orders[data] = None

    def notify_trade(self, trade):
        """交易通知"""
        if not trade.isclosed:
            return
        self.log(f"OPERATION PROFIT, GROSS {trade.pnl:.2f}, NET {trade.pnlcomm:.2f}, " f"Stock: {trade.data._name}")

    # 你可以在这里继续添加更多的策略特定的方法和逻辑
