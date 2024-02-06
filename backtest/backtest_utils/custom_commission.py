import backtrader as bt


class CustomCommissionSchema(bt.CommInfoBase):
    """
    佣金类型：买入时佣金万分之三，卖出时佣金万分之三加千分之一印花税, 每笔交易佣金最低扣5块钱
    """

    params = (
        ("commission", 0.0003),  # 买入时的佣金率
        ("stamp_duty", 0.001),  # 印花税率
        ("min_comm", 5.0),  # 最低佣金
    )

    def _getcommission(self, size, price, pseudoexec):
        """计算佣金的函数"""
        # 根据买卖方向计算基础佣金
        if size > 0:  # 买入
            comm = size * price * self.params.commission
        elif size < 0:  # 卖出
            comm = size * price * (self.params.commission + self.params.stamp_duty)
        else:  # size == 0，没有交易
            return 0
        # 最低佣金的处理
        if abs(comm) < self.params.min_comm:
            return self.params.min_comm
        return abs(comm)  # 返回正数佣金
