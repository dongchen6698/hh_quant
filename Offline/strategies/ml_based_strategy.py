import backtrader as bt
import pandas as pd
from tqdm import tqdm
from .base_strategy import BaseStrategy


class CustomMLStrategy(BaseStrategy):
    params = (
        ("top_n", 3),
        ("take_profit_min_threshold", 0.0),
        ("stop_loss_max_threshold", -0.0),
        ("model_pred_dataframe", pd.DataFrame()),
    )

    def __init__(self):
        # 初始化父类方法 & 参数
        super().__init__()  # 调用基础策略的初始化方法
        self.stock_for_buy, self.stock_for_sell = self.get_model_prediction()

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

    def buy_top_predicted_stocks(self, data, selected_stocks):
        if data._name in selected_stocks:
            size = self.get_position_size_with_atr(data)  # 使用ATR计算仓位大小
            if size > 0:
                self.buy(data=data, size=size, exectype=bt.Order.Market)

    def sell_bottom_predicted_stocks(self, data, selected_stocks):
        if data._name in selected_stocks:
            size = self.getposition(data).size
            self.close(data=data, size=size, exectype=bt.Order.Market)

    def next(self):
        # 获取当前日期
        current_date = self.datas[0].datetime.date(0).strftime("%Y-%m-%d")  # 格式化日期
        # 获取当前日期的预测的top_n名单
        buy_stocks = self.stock_for_buy.get(current_date, [])
        sell_stocks = self.stock_for_sell.get(current_date, [])
        # 遍历每个数据集
        for data in self.datas:
            # 检查是否有挂起的订单
            if self.orders[data]:
                continue
            # 检查是否持有当前股票
            data_position = self.getposition(data).size
            if not data_position:
                self.buy_top_predicted_stocks(data, buy_stocks)
            else:
                # self.sell_bottom_predicted_stocks(data, sell_stocks)
                self.manage_risk_with_atr(data)
