import backtrader as bt
import pandas as pd
from .base_strategy import BaseStrategy


class CustomMLStrategy(BaseStrategy):
    params = {
        "top_n": 3,
        "take_profit_min_threshold": 0.0,
        "stop_loss_max_threshold": -0.0,
        "model_pred_dataframe": pd.DataFrame(),
        "max_holding_period": 5,
        "atr_period": 7,
        "atr_take_profit_multiplier": 2,
        "atr_stop_loss_multiplier": 1,
        "atr_risk_percent": 0.01,
    }

    def __init__(self):
        # 初始化父类方法 & 参数
        super().__init__()  # 调用基础策略的初始化方法
        self.atrs = {data: bt.indicators.AverageTrueRange(data, period=self.params.atr_period) for data in self.datas}  # 计算ATR相关指标
        self.stock_for_buy, self.stock_for_sell = self.get_model_prediction()
        self.holding_period = {}  # 新增字典来追踪持仓天数

    def get_model_prediction(self):
        def get_stock_for_buy(group):
            filtered_group = group[group["future_return_pred"] >= self.params.take_profit_min_threshold]
            top_n = filtered_group.nlargest(self.params.top_n, "future_return_pred")
            return top_n["stock_code"].tolist()

        def get_stock_for_sell(group):
            filtered_group = group[group["future_return_pred"] <= self.params.stop_loss_max_threshold]
            bottom_n = filtered_group.nsmallest(self.params.top_n, "future_return_pred")
            return bottom_n["stock_code"].tolist()

        # model_prediction = pd.read_pickle(self.params.model_prediction_file)
        model_prediction = self.params.model_pred_dataframe
        model_prediction["stock_code"] = model_prediction["stock_code"].map(lambda x: str(x).zfill(6))
        stock_for_buy = model_prediction.groupby("datetime").apply(get_stock_for_buy).to_dict()
        stock_for_sell = model_prediction.groupby("datetime").apply(get_stock_for_sell).to_dict()
        return stock_for_buy, stock_for_sell

    def get_position_size_with_atr(self, data):
        try:
            # 获取ATR值，确保ATR值是有效的
            atr_value = self.atrs.get(data, [None])[0]
            # 计算止损价格差，确保止损乘数是正数
            stop_loss = self.params.atr_stop_loss_multiplier * atr_value
            # 获取当前账户现金，确保现金量是有效的
            cash = self.broker.get_cash()
            # 计算风险金额，确保风险百分比在0和1之间
            risk_percent = self.params.atr_risk_percent
            risk_amount = cash * risk_percent
            # 计算仓位大小，并返回整数部分的股数
            size = risk_amount / stop_loss
            return int(size)
        except ValueError as e:
            # 处理异常，例如打印错误信息
            print(f"计算仓位时出现错误: {e}")
            # 出现错误时，可以选择返回零或其他合适的默认值
            return 0

    def next(self):
        # 获取当前日期
        current_date = self.datas[0].datetime.date(0).strftime("%Y-%m-%d")  # 格式化日期
        # 获取当前日期的预测的top_n名单
        today_buy_stocks = self.stock_for_buy.get(current_date, [])
        today_sell_stocks = self.stock_for_sell.get(current_date, [])
        # 遍历每个数据集
        for data in self.datas:
            # 检查是否有挂起的订单
            if self.orders[data]:
                continue
            # 检查是否持有当前股票
            data_position = self.getposition(data)
            if not data_position:
                # 检查买入条件
                buy_condition_1 = data._name in today_buy_stocks  # 模型预测TopN
                if buy_condition_1:
                    size = self.get_position_size_with_atr(data)  # 使用ATR计算仓位大小
                    if size > 0:
                        self.buy(data=data, size=size, exectype=bt.Order.Market)
                        self.holding_period[data._name] = 1  # 初始化持仓天数
            else:
                # 检查卖出条件
                sell_condition_1 = data._name in today_sell_stocks  # 模型预测BottomN
                sell_condition_2 = (
                    data.close[0] > data_position.price + self.params.atr_take_profit_multiplier * self.atrs[data][0]
                )  # 买入价格 + 2 * ATR作为止盈上限
                self_condition_3 = (
                    data.close[0] < data_position.price - self.params.atr_stop_loss_multiplier * self.atrs[data][0]
                )  # 买入价格 - 1 * ATR作为止损下限
                sell_condition_4 = self.holding_period.get(data._name, 0) >= self.params.max_holding_period  # 达到最大持仓周期
                if sell_condition_1 or sell_condition_2 or self_condition_3 or sell_condition_4:
                    self.log(f"模型预测: {sell_condition_1}, 止盈: {sell_condition_2}, 止损: {self_condition_3}, 最大持仓周期: {sell_condition_4}")
                    self.close(data=data, exectype=bt.Order.Market)
