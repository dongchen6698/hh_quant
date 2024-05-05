import backtrader as bt
import pandas as pd
import math

from .base_strategy import BaseStrategy
from copy import deepcopy


class CustomMLStrategy(BaseStrategy):
    params = {
        "model_pred_dataframe": pd.DataFrame(),
        "max_position_proportion": 0.1,  # 最大持仓资金占比
        "min_holding_period": 3,  # 最小持仓周期
        "max_holding_period": 30,  # 最大持仓周期
        "top_n": 3,  # 每日选择股票的TopN
        "min_buy_cash": 1000,  # 最小购买资金限制
        "atr_period": 14,  # ATR计算周期
        "atr_take_profit_factor": 3,  # ATR止盈因子
        "atr_stop_loss_factor": 2,  # ATR止损因子
        "atr_risk": 0.1,  # ATR风险系数
        "label_pred_threshold": 0.0,  # 人工定义的预测threshold
    }

    def __init__(self):
        super().__init__()  # 调用基础策略的初始化方法
        # 计算ATR
        self.atr = {data: bt.indicators.AverageTrueRange(deepcopy(data), period=self.params.atr_period) for data in self.datas}
        # 获取模型预测
        self.stock_for_buy = self.get_model_prediction()
        self.holding_period = {}

    def get_model_prediction(self):
        def get_stock_for_buy(group):
            group = group[group["label_pred"] > self.params.label_pred_threshold]
            top_n = group.nlargest(self.params.top_n, "label_pred")
            return top_n.to_dict("records")

        model_prediction = self.params.model_pred_dataframe
        stock_for_buy = model_prediction.groupby("datetime").apply(get_stock_for_buy).to_dict()
        return stock_for_buy

    def next(self):
        # 获取当前日期
        current_date = self.datas[0].datetime.date(0).isoformat()
        print(f"current_date: {current_date} ================================================================================")
        # 获取当前日期预测的买入名单
        today_buy_stocks = [i.get("stock_code") for i in self.stock_for_buy.get(current_date, [])]
        print(f"today_buy_stocks: {today_buy_stocks}")
        # 获取当前可用现金
        today_avaiable_cash = self.broker.getcash()
        print(f"current_cash: {today_avaiable_cash}")

        # 卖出操作
        for data in self.getpositions():
            position = self.getpositionbyname(data._name)
            holding_condition = self.holding_period.get(data._name, 0) >= self.params.min_holding_period
            if position.size > 0 and holding_condition:  # 满足持仓 + 最小持仓周期限制
                sell_condition_1 = data.high[0] > position.price + self.params.atr_take_profit_factor * self.atr[data][0]  # ATR止盈
                sell_condition_2 = data.low[0] < position.price - self.params.atr_stop_loss_factor * self.atr[data][0]  # ATR止损
                sell_condition_3 = self.holding_period.get(data._name, 0) >= self.params.max_holding_period  # 最大持仓周期
                if sell_condition_1 or sell_condition_2 or sell_condition_3:
                    self.close(data=data, exectype=bt.Order.Market)
                    self.holding_period.pop(data._name, None)

                # if sell_condition_1:  # 如果满足止盈则阶梯式卖出
                #     position_value = self.broker.get_value(datas=[data])
                #     if position_value > self.params.min_buy_cash:
                #         self.sell(data=data, size=position.size // 2, exectype=bt.Order.Market)
                #     else:
                #         self.close(data=data, exectype=bt.Order.Market)
                #         self.holding_period.pop(data._name, None)
                # elif sell_condition_2 or sell_condition_3:  # 如果满足止损或最大持仓周期，则直接平仓
                #     self.close(data=data, exectype=bt.Order.Market)
                #     self.holding_period.pop(data._name, None)

        # 买入操作
        if len(today_buy_stocks) > 0:
            today_stock_weights = [1 / math.log(i + 2) for i in range(len(today_buy_stocks))]
            today_stock_weights = [w / sum(today_stock_weights) for w in today_stock_weights]  # Norm
            for i, stock_code in enumerate(today_buy_stocks):
                data = self.getdatabyname(stock_code)
                position = self.getpositionbyname(stock_code)
                avaiable_cash = today_avaiable_cash * today_stock_weights[i]  # 当前可用资金 * 当前stock权重占比
                max_position_value = self.broker.get_value() * self.params.max_position_proportion  # 最大持仓价值
                # 检测是否已经有持仓
                if position.size > 0:
                    # 计算当前价值
                    max_remain_cash = max_position_value - self.broker.get_value(datas=[data])  # 如果再买同一stock的话，最多能用多少资金
                    avaiable_cash = min(avaiable_cash, max_remain_cash)  # 选择最终可用金额
                else:
                    # 确保不超过总资产的10%
                    avaiable_cash = min(avaiable_cash, max_position_value)  # 选择最终可用金额
                if avaiable_cash > self.params.min_buy_cash:  # 确保开仓金额不小于条件限定
                    if self.atr[data][0] > 0:
                        # 计算size
                        base_size = int(avaiable_cash / data.close[0])  # 计算可用金额下的size
                        atr_size = int((avaiable_cash * self.params.atr_risk) / self.atr[data][0])  # 考虑风险后的size
                        self.buy(data=data, size=min(base_size, atr_size), exectype=bt.Order.Market)  # 使用最小风险的size=min(base_size, atr_size)
                        self.holding_period[stock_code] = 1  # 初始化+更新持仓周期

        # 更新目前的持仓周期
        for k in list(self.holding_period.keys()):
            self.holding_period[k] += 1
