import backtrader as bt
import pandas as pd
from .base_strategy import BaseStrategy


class CustomMLStrategy(BaseStrategy):
    params = (
        ("take_profit_percent", 0.15),
        ("stop_loss_percent", -0.03),
        ("max_holding_period", 5),
        ("top_n", 3),
        ("model_prediction_file", ""),
    )

    def __init__(self):
        # 初始化父类方法 & 参数
        super().__init__()  # 调用基础策略的初始化方法
        self.model_prediction = pd.read_pickle(self.params.model_prediction_file)
        self.model_prediction["stock_code"] = self.model_prediction["stock_code"].map(lambda x: str(x).zfill(6))
        self.holding = {}

    def manage_position(self):
        def check_stop_loss(stock_name):
            data = self.getdatabyname(stock_name)
            position = self.getposition(data)
            stop_price = position.price * (1 + self.params.stop_loss_percent)
            current_price = data.close[0]
            if position:
                if current_price < stop_price:
                    self.log(
                        f"触发止损【position_price: {position.price:.2f}, stop_price: {stop_price:.2f}, current_price: {current_price:.2f}】，执行平仓，股票:{data._name}"
                    )
                    self.close(data=data, size=position.size, exectype=bt.Order.Market)

        def check_table_profit(stock_name):
            data = self.getdatabyname(stock_name)
            position = self.getposition(data)
            stop_price = position.price * (1 + self.params.take_profit_percent)
            current_price = data.close[0]
            if position:
                if current_price > stop_price:
                    self.log(
                        f"触发止盈【position_price: {position.price:.2f}, stop_price: {stop_price:.2f}, current_price: {current_price:.2f}】，执行平仓，股票:{data._name}"
                    )
                    self.close(data=data, size=position.size, exectype=bt.Order.Market)

        def check_max_holding_period(stock_name):
            data = self.getdatabyname(stock_name)
            position = self.getposition(data)
            self.holding.setdefault(stock_name, 0)
            self.holding[stock_name] += 1
            if position:
                if self.holding[stock_name] > self.params.max_holding_period:
                    self.log(f"触发最大持仓周期【holding_period: {self.holding[stock_name]}】，执行平仓，股票:{data._name}")
                    self.close(data=data, size=position.size, exectype=bt.Order.Market)
                    self.holding[stock_name] = 0  # Reset holding period

        current_positions = [data._name for data in self.datas if self.getposition(data).size > 0]
        for stock_name in current_positions:
            check_stop_loss(stock_name)
            check_table_profit(stock_name)
            check_max_holding_period(stock_name)

    def buy_top_predicted_stocks(self):
        # 获取前一个交易日预测的今日结果
        today_predictions = self.model_prediction[self.model_prediction["datetime"] == self.datas[0].datetime.date(0).isoformat()]
        # selected_stocks = today_predictions[
        #     (today_predictions["max_return_pred"] > self.params.take_profit_percent) & (today_predictions["min_return_pred"] > self.params.stop_loss_percent)
        # ].nlargest(self.params.top_n, "max_return_pred")
        selected_stocks = today_predictions.nlargest(self.params.top_n, "norm_return_pred")

        current_positions = [data._name for data in self.datas if self.getposition(data).size > 0]
        for _, row in selected_stocks.iterrows():
            stock_code = row["stock_code"]
            if stock_code not in current_positions:
                data = self.getdatabyname(stock_code)
                if data:
                    # print(row)x
                    self.buy(data=data, exectype=bt.Order.Market)
                    self.holding[stock_code] = 0  # Initialize holding period

    def next(self):
        self.manage_position()
        self.buy_top_predicted_stocks()
