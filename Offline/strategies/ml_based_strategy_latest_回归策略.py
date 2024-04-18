import backtrader as bt
import pandas as pd
import math

from .base_strategy import BaseStrategy
from copy import deepcopy


class CustomMLStrategy(BaseStrategy):
    """_summary_
        * 1. 如何动态调整每日买入卖出数量？根据模型预测概率or其他
        * 2. 如何更高效的应用资金管理策略？凯利公式？
        * 3. 止盈止损逻辑 + 打散策略（多元化、行业打散等）
    Args:
        BaseStrategy (_type_): _description_
    Returns:
        _type_: _description_
    """

    params = {
        "model_pred_dataframe": pd.DataFrame(),
        "max_cash_per_instrument": 0.1,
        "max_holding_period": 30,
        "buy_top_n": 3,
        "sell_top_n": 3,
        "min_buy_size": 100,
        "atr_period": 14,
        "atr_risk": 0.1,
    }

    def __init__(self):
        super().__init__()  # 调用基础策略的初始化方法
        self.atr = {data: bt.indicators.AverageTrueRange(deepcopy(data), period=self.params.atr_period) for data in self.datas}
        # 计算TopBuyN股票的权重（非等权）
        self.stock_weights = [1 / math.log(i + 2) for i in range(self.params.buy_top_n)]
        self.stock_weights = [w / sum(self.stock_weights) for w in self.stock_weights]  # Norm
        # 获取模型预测
        self.stock_for_buy, self.stock_for_sell = self.get_model_prediction()
        self.holding_period = {}

    def get_model_prediction(self):
        def get_stock_for_buy(group):
            filtered_group = group[group["label_pred"] > 0.0]
            top_n = filtered_group.nlargest(self.params.buy_top_n, "label_pred")
            return top_n.to_dict("records")

        def get_stock_for_sell(group):
            filtered_group = group[group["label_pred"] < 0.0]
            bottom_n = filtered_group.nsmallest(self.params.sell_top_n, "label_pred")
            return bottom_n.to_dict("records")

        model_prediction = self.params.model_pred_dataframe
        stock_for_buy = model_prediction.groupby("datetime").apply(get_stock_for_buy).to_dict()
        stock_for_sell = model_prediction.groupby("datetime").apply(get_stock_for_sell).to_dict()
        return stock_for_buy, stock_for_sell

    def next(self):
        # 获取当前日期
        current_date = self.datas[0].datetime.date(0).isoformat()
        print(f"current_date: {current_date} ================================================================================")
        # 获取当前日期预测的买入名单
        today_buy_stocks = [i.get("stock_code") for i in self.stock_for_buy.get(current_date, [])]
        print(f"today_buy_stocks: {today_buy_stocks}")
        # 获取当前日期预测的卖出名单
        today_sell_stocks = [i.get("stock_code") for i in self.stock_for_sell.get(current_date, [])]
        print(f"today_sell_stocks: {today_sell_stocks}")
        # 获取当前可用现金
        current_cash = self.broker.getcash()
        print(f"current_cash: {current_cash}")
        print(f"current_position: {self.holding_period}")

        # 卖出操作
        for data in self.getpositions():
            position = self.getpositionbyname(data._name)
            if position.size > 0:
                sell_condition_1 = data._name in today_sell_stocks
                sell_condition_2 = data.close[0] > position.price + 3 * self.atr[data][0]  # ATR止盈
                sell_condition_3 = data.close[0] < position.price - 2 * self.atr[data][0]  # ATR止损
                sell_condition_4 = self.holding_period.get(data._name, 0) > self.params.max_holding_period  # 最大持仓周期
                final_sell_condition = sell_condition_1
                if final_sell_condition:
                    if position.size < 100:
                        self.close(data=data, exectype=bt.Order.Market)
                        self.holding_period.pop(data._name, None)
                    else:
                        self.sell(data=data, size=position.size // 2, exectype=bt.Order.Market)

        # 买入操作
        for i, stock_code in enumerate(today_buy_stocks):
            data = self.getdatabyname(stock_code)
            avaiable_cash = current_cash * self.stock_weights[i]
            avaiable_cash = min(avaiable_cash, self.broker.getvalue() * self.params.max_cash_per_instrument)
            size = int(avaiable_cash / data.close[0])
            if self.atr[data][0] > 0:
                size_atr = int((avaiable_cash * self.params.atr_risk) / self.atr[data][0])
                size = min(size_atr, size)
                if size > self.params.min_buy_size:  # 最少股数量
                    self.buy(data=data, size=size, exectype=bt.Order.Market)
                    self.holding_period[stock_code] = 1

        # 更新操作
        for k in self.holding_period.keys():
            self.holding_period[k] += 1
