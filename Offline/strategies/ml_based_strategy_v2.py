import backtrader as bt
import pandas as pd
from .base_strategy import BaseStrategy


class CustomMLStrategy(BaseStrategy):
    params = {
        "top_n": 5,
        "bottom_n": 5,
        "model_pred_dataframe": pd.DataFrame(),
        "max_holding_period": 10,
        "max_holding_count": 10,
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
            filtered_group = group[group["pred_label"] == 1]
            top_n = filtered_group.nlargest(self.params.top_n, "pred_label_1_prob")
            return top_n.to_dict("records")

        def get_stock_for_sell(group):
            filtered_group = group[group["pred_label"] == 2]
            bottom_n = filtered_group.nlargest(self.params.bottom_n, "pred_label_2_prob")
            return bottom_n.to_dict("records")

        model_prediction = self.params.model_pred_dataframe
        model_prediction["stock_code"] = model_prediction["stock_code"].map(lambda x: str(x).zfill(6))
        stock_for_buy = model_prediction.groupby("datetime").apply(get_stock_for_buy).to_dict()
        stock_for_sell = model_prediction.groupby("datetime").apply(get_stock_for_sell).to_dict()
        return stock_for_buy, stock_for_sell

    def get_position_size_with_atr(self, data, cash):
        # 获取ATR值，确保ATR值是有效的
        atr_value = self.atrs.get(data)[0]
        if atr_value == 0:
            return 0
        # 计算止损价格差，确保止损乘数是正数
        stop_loss = self.params.atr_stop_loss_multiplier * atr_value
        # 计算风险金额，确保风险百分比在0和1之间
        risk_percent = self.params.atr_risk_percent
        risk_amount = cash * risk_percent
        # 计算仓位大小，并返回整数部分的股数
        size = int(risk_amount / stop_loss)
        return size if size > 0 else 0

    def check_stock_positions(self, position_pool, data_map, sell_pool):
        for stock_code in list(position_pool):
            data = data_map.get(stock_code, None)
            position = self.getpositionbyname(stock_code)
            if data:
                take_profit_condition = data.close[0] > position.price + self.params.atr_take_profit_multiplier * self.atrs[data][0]
                stop_loss_condition = data.close[0] < position.price - self.params.atr_stop_loss_multiplier * self.atrs[data][0]
                model_sell_condition = stock_code in sell_pool
                holding_period_condition = self.holding_period.get(stock_code, 0) >= self.params.max_holding_period
                if take_profit_condition:
                    self.log(f"触发止盈限制：{data._name}")
                    self.close(data=data, exectype=bt.Order.Market)
                    self.holding_period.pop(stock_code, None)
                    continue
                if stop_loss_condition:
                    self.log(f"触发止损限制：{data._name}")
                    self.close(data=data, exectype=bt.Order.Market)
                    self.holding_period.pop(stock_code, None)
                    continue
                if model_sell_condition:
                    self.log(f"触发模型限制：{data._name}")
                    self.close(data=data, exectype=bt.Order.Market)
                    self.holding_period.pop(stock_code, None)
                    continue
                if holding_period_condition:
                    self.log(f"触发持仓限制：{data._name}")
                    self.close(data=data, exectype=bt.Order.Market)
                    self.holding_period.pop(stock_code, None)
                    continue

    def check_stock_buy(self, position_pool, data_map, buy_pool):
        current_holding_count = len(self.holding_period.keys())
        if self.params.max_holding_count > current_holding_count:
            remain_position_count = self.params.max_holding_count - current_holding_count
            available_cash_per_stock = self.broker.get_cash() / remain_position_count
            available_stock_count = min(remain_position_count, self.params.top_n)
            for stock_code in buy_pool[:available_stock_count]:
                if stock_code in position_pool:
                    self.holding_period[stock_code] = 0  # 更新
                else:
                    data = data_map.get(stock_code, None)
                    if data:
                        buy_size = self.get_position_size_with_atr(data, available_cash_per_stock)
                        if buy_size > 0:
                            self.buy(data=data, size=buy_size, exectype=bt.Order.Market)
                            self.holding_period[data._name] = 0  # 初始化持仓天数

    def next(self):
        # 0. 获取当前日期
        current_date = self.datas[0].datetime.date(0).isoformat()  # 格式化日期
        # 1. 获取今日的操作股票池
        today_buy_pool = [i.get("stock_code") for i in self.stock_for_buy.get(current_date, [])]
        today_sell_pool = [i.get("stock_code") for i in self.stock_for_sell.get(current_date, [])]
        today_position_pool = list(self.holding_period.keys())
        today_operate_pool = set(today_position_pool + today_buy_pool + today_sell_pool)
        today_operate_data_map = {data._name: data for data in self.datas if data._name in today_operate_pool}

        # 2. 检查并执行卖出操作
        self.check_stock_positions(today_position_pool, today_operate_data_map, today_sell_pool)

        # 3. 检查并执行买入操作
        # 注意：现在持仓数量已经可能由于卖出操作而改变，需要重新计算
        updated_position_pool = list(self.holding_period.keys())
        self.check_stock_buy(updated_position_pool, today_operate_data_map, today_buy_pool)

        # 4. 更新持仓天数
        for stock_code in self.holding_period.keys():
            self.holding_period[stock_code] += 1
