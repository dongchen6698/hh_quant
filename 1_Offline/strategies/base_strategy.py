import backtrader as bt
from risk_management import RiskManager


class BaseStrategy(bt.Strategy):
    params = {
        "log_file": None,
        "benchmark": None,
        "risk_manage": False,
    }

    def __init__(self):
        # 初始化数据 & 基准
        if self.params.benchmark is not None:
            print("启动基准对比...")
            self.benchmark = self.getdatabyname(self.params.benchmark)  # 选择基准数据
            self.datas = [data for data in self.datas if data._name != self.params.benchmark]  # 过滤基准数据

        # 初始化风险管理
        if self.params.risk_manage:
            print("启动风险控制...")
            self.risk_manager = RiskManager(self)

        # 使用字典跟踪每个数据源的订单、买入价格和佣金
        self.orders = {data: None for data in self.datas}
        self.buyprice = {data: None for data in self.datas}
        self.buycomm = {data: None for data in self.datas}
        # 在这里为每个数据源添加通用指标的初始化

    def log(self, txt, dt=None, doprint=True):
        """日志记录函数"""
        if self.params.log_file or doprint:
            dt = dt or self.datas[0].datetime.date(0)  # 默认使用第一个数据源的日期
            print(f"{dt.isoformat()} {txt}")  # 打印日期和日志信息

    def notify_order(self, order):
        """订单状态通知"""
        data = order.data  # 获取与订单关联的数据源
        if order.status in [order.Submitted, order.Accepted]:
            # 订单已提交或已被接受
            return
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(
                    f"买入执行, 引用: {order.ref}, 价格: {order.executed.price:.2f}, "
                    f"成本: {order.executed.value:.2f}, 手续费: {order.executed.comm:.2f}, "
                    f"数量: {order.executed.size:.2f}, 股票: {data._name}"
                )
                self.buyprice[data] = order.executed.price
                self.buycomm[data] = order.executed.comm
            elif order.issell():
                self.log(
                    f"卖出执行, 引用: {order.ref}, 价格: {order.executed.price:.2f}, "
                    f"成本: {order.executed.value:.2f}, 手续费: {order.executed.comm:.2f}, "
                    f"数量: {order.executed.size:.2f}, 股票: {data._name}"
                )
            self.orders[data] = None
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log("订单取消/保证金不足/拒绝")
            self.orders[data] = None

    def notify_trade(self, trade):
        """交易通知"""
        if not trade.isclosed:
            return
        self.log(f"操作盈亏, 毛利润: {trade.pnl:.2f}, 净利润: {trade.pnlcomm:.2f}, 股票: {trade.data._name}")
