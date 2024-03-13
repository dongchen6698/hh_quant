import backtrader as bt


class BaseStrategy(bt.Strategy):
    params = {
        "log_file": None,
        "benchmark": None,
        "risk_manage": True,
        "atr_period": 7,
        "atr_take_profit_multiplier": 2,  # 2 * ATR作为止盈上限
        "atr_stop_loss_multiplier": 1,  # 1 * ATR作为止损下限
        "atr_risk_percent": 0.01,  # 风险0.01表示每次交易最多风险账户的1%
    }

    def __init__(self):
        # 初始化数据 & 基准
        if self.params.benchmark is not None:
            print("启动基准对比...")
            self.benchmark = self.getdatabyname(self.params.benchmark)  # 选择基准数据
            self.datas = [data for data in self.datas if data._name != self.params.benchmark]  # 过滤基准数据
            print(f"回测数据共: {len(self.datas)}")
        # 是否启用风险管理
        if self.params.risk_manage:
            print(f"开始计算ATR相关指标")
            self.atrs = {data: bt.indicators.AverageTrueRange(data, period=self.params.atr_period) for data in self.datas}

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

    def manage_risk_with_atr(self, data):
        """基于ATR的风险管理方法"""
        position = self.getposition(data)
        if position:
            atr_value = self.atrs[data][0]  # 当前ATR值
            # 计算止盈和止损价格
            take_profit_price = position.price + self.params.atr_take_profit_multiplier * atr_value  # 买入价格 + 2 * ATR作为止盈上限
            stop_loss_price = position.price - self.params.atr_stop_loss_multiplier * atr_value  # 买入价格 - 1 * ATR作为止损下限
            # 检查止盈和止损条件
            if data.close[0] > take_profit_price:
                self.log(f"ATR 触发止盈... 执行平仓【股票: {data._name}】, 购入价格: {position.price}, 止盈价格: {take_profit_price}】")
                self.close(data=data, size=position.size, exectype=bt.Order.Market)
            elif data.close[0] < stop_loss_price:
                self.log(f"ATR 触发止损... 执行平仓【股票: {data._name}】, 购入价格: {position.price}, 止损价格: {stop_loss_price}】")
                self.close(data=data, size=position.size, exectype=bt.Order.Market)

    def get_position_size_with_atr(self, data):
        """根据ATR计算仓位大小"""
        atr_value = self.atrs[data][0]  # 获取ATR值
        stop_loss = self.params.atr_stop_loss_multiplier * atr_value  # 计算止损价格差
        # 计算风险金额
        cash = self.broker.get_cash()  # 获取当前账户现金
        risk_amount = cash * self.params.atr_risk_percent  # 风险金额是账户现金的一小部分
        # 计算仓位大小
        size = risk_amount / stop_loss  # 仓位大小是风险金额除以每股风险
        return int(size)  # 返回整数部分的股数
