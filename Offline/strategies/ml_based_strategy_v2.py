import backtrader as bt
import pandas as pd
from .base_strategy import BaseStrategy


import backtrader as bt
import pandas as pd
import math
from copy import deepcopy


class CustomMLStrategy(BaseStrategy):
    params = {
        "model_pred_dataframe": pd.DataFrame(),
        "max_cash_per_instrument": 0.2,
        "top_n": 5,
        "min_size": 100,
        "atr_period": 7,
        "atr_take_profit_factor": 2,
        "atr_stop_loss_factor": 1,
    }

    def __init__(self):
        super().__init__()  # 调用基础策略的初始化方法
        self.atr = {data: bt.indicators.AverageTrueRange(deepcopy(data), period=self.params.atr_period) for data in self.datas}
        self.stock_for_buy, self.stock_for_sell = self.get_model_prediction()  # 获取模型预测

    def get_model_prediction(self):
        def get_stock_for_buy(group):
            filtered_group = group[group["label_pred"] > 0.0]
            top_n = filtered_group.nlargest(self.params.top_n, "label_pred")
            return top_n.to_dict("records")

        def get_stock_for_sell(group):
            filtered_group = group[group["label_pred"] < 0.0]
            bottom_n = filtered_group.nsmallest(self.params.top_n, "label_pred")
            return bottom_n.to_dict("records")

        model_prediction = self.params.model_pred_dataframe
        model_prediction["stock_code"] = model_prediction["stock_code"].map(lambda x: str(x).zfill(6))
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

        # 遍历预定的买入股票
        if len(today_buy_stocks):
            cash_per_stock = current_cash / len(today_buy_stocks)
            cash_per_stock = min(cash_per_stock, self.broker.getvalue() * self.params.max_cash_per_instrument)
            cash_risk_per_stock = cash_per_stock * 0.1
            for stock_code in today_buy_stocks:
                data = self.getdatabyname(stock_code)
                if self.atr[data][0] > 0:
                    size_1 = int(cash_risk_per_stock / self.atr[data][0])
                else:
                    size_1 = 0
                size_2 = int(cash_per_stock / data.close[0])
                size = min(size_1, size_2)
                if size > self.params.min_size:
                    self.buy(data=data, size=size, exectype=bt.Order.Market)

        # 检查是否需要卖出股票
        for pos in self.getpositions():
            data = self.getdatabyname(pos._name)
            position = self.getpositionbyname(pos._name)
            # 检查止盈
            take_profit_condition = data.close[0] > position.price + 2 * self.atr[data][0]
            # 检查止损
            stop_loss_condition = data.close[0] < position.price - 1 * self.atr[data][0]
            # 卖出操作
            if take_profit_condition or stop_loss_condition:
                self.close(data=data, exectype=bt.Order.Market)
