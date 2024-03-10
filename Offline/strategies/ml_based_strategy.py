import backtrader as bt
import pandas as pd
from .base_strategy import BaseStrategy


class CustomMLStrategy(BaseStrategy):
    params = (
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
        if self.params.risk_manage:
            # 使用BaseStrategy的ATR风险控制方法管理仓位
            for data in self.datas:
                self.manage_risk_with_atr(data)

    def buy_top_predicted_stocks(self):
        today_predictions = self.model_prediction[self.model_prediction["datetime"] == self.datas[0].datetime.date(0).isoformat()]
        selected_stocks = today_predictions.nlargest(self.params.top_n, "future_return_pred")
        current_positions = [data._name for data in self.datas if self.getposition(data).size > 0]
        for _, row in selected_stocks.iterrows():
            stock_code = row["stock_code"]
            if stock_code not in current_positions:
                data = self.getdatabyname(stock_code)
                if data:
                    size = self.get_position_size_with_atr(data)  # 使用ATR计算仓位大小
                    if size > 0:
                        self.buy(data=data, size=size, exectype=bt.Order.Market)
                        self.holding[stock_code] = 1  # Initialize holding period

    def next(self):
        self.manage_position()
        self.buy_top_predicted_stocks()
