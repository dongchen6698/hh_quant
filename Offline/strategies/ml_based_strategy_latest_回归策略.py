import backtrader as bt
import pandas as pd
import math

from .base_strategy import BaseStrategy
from copy import deepcopy


class CustomMLStrategy(BaseStrategy):
    params = {
        "model_pred_dataframe": pd.DataFrame(),
        "max_position_proportion": 0.15,  # 最大持仓资金占比
        "min_holding_period": 3,  # 最小持仓周期
        "max_holding_period": 20,  # 最大持仓周期
        "top_n": 3,  # 每日选择股票的TopN
        "min_buy_cash": 2000,  # 最小购买资金限制
        "atr_period": 14,  # ATR计算周期
        "init_trailing_stop_loss_factor": 1.5,  # 首次买入跟踪止损位 = 1.5ATR
        "update_trailing_stop_loss_factor": 1,  # 更新跟踪止损位 = 1ATR
        "atr_risk": 0.05,  # ATR风险系数
        "buy_pred_upper_bound": 0.58,  # 使用模型预测打分的分布（> 0.9的quantile）进行买入过滤
        "sell_pred_lower_bound": 0.37,  # 使用模型预测打分的分布（< 0.1的quantile）进行卖出过滤
    }

    def __init__(self):
        super().__init__()  # 调用基础策略的初始化方法
        # 计算ATR
        self.atr = {data: bt.indicators.AverageTrueRange(deepcopy(data), period=self.params.atr_period) for data in self.datas}
        # 获取模型预测
        self.stock_for_buy, self.stock_for_sell = self.get_model_prediction(self.params.model_pred_dataframe)
        self.trailing_stop_loss = {}
        self.holding_period = {}

    def get_model_prediction(self, model_prediction):
        def get_stock_for_buy(group):
            group = group[group["label_pred"] > self.params.buy_pred_upper_bound]  # 使用模型预测打分的分布（> 0.9的quantile）进行买入过滤
            select_n = group.nlargest(self.params.top_n, "label_pred")
            return select_n.to_dict("records")

        def get_stock_for_sell(group):
            group = group[group["label_pred"] < self.params.sell_pred_lower_bound]  # 使用模型预测打分的分布（< 0.1的quantile）进行卖出过滤
            select_n = group.nsmallest(self.params.top_n, "label_pred")
            return select_n.to_dict("records")

        stock_for_buy = model_prediction.groupby("datetime").apply(get_stock_for_buy).to_dict()
        stock_for_sell = model_prediction.groupby("datetime").apply(get_stock_for_sell).to_dict()
        return stock_for_buy, stock_for_sell

    def next(self):
        # 1. 初始化当日相关信息
        # 1.1 获取当前日期
        current_date = self.datas[0].datetime.date(0).isoformat()
        print(f"current_date: {current_date} ================================================================================")
        # 1.2 获取当前日期预测的买入卖出名单
        today_buy_stocks = {i["stock_code"]: i for i in self.stock_for_buy.get(current_date, [])}
        today_sell_stocks = {i["stock_code"]: i for i in self.stock_for_sell.get(current_date, [])}
        # 1.3 获取当前可用现金
        today_avaiable_cash = self.broker.get_cash()
        print(f"current_cash: {today_avaiable_cash}")

        # 2. 检查卖出操作
        for data in self.getpositions():
            position = self.getpositionbyname(data._name)
            holding_condition = self.holding_period.get(data._name, 0) > self.params.min_holding_period
            if position.size > 0 and holding_condition:  # 满足持仓 + 最小持仓周期限制
                # 2.1 模型预测卖出条件
                # sell_condition_1 = data._name in today_sell_stocks.keys()
                sell_condition_1 = False
                # 2.2 动态跟踪止损
                sell_condition_2 = data.low[0] < self.trailing_stop_loss[data._name]  # 使用跟踪止损作为卖出条件
                if not sell_condition_2:
                    # 如果未触发止损，则更新跟踪止损线
                    self.trailing_stop_loss[data._name] = max(
                        self.trailing_stop_loss[data._name],  # 原始止损线
                        data.low[0] - self.params.update_trailing_stop_loss_factor * self.atr[data][0],  # 新止损线
                    )
                    self.holding_period[data._name] = 1  # 重定义持仓天数
                # 2.3 最大持仓周期条件
                sell_condition_3 = self.holding_period.get(data._name, 0) >= self.params.max_holding_period
                # 3. 条件检查（触发任意卖出限制，则进行清仓处理）
                if sell_condition_1 or sell_condition_2 or sell_condition_3:
                    self.close(data=data, exectype=bt.Order.Market)
                    # 更新维护的dict信息
                    self.trailing_stop_loss.pop(data._name, None)
                    self.holding_period.pop(data._name, None)

        # 3. 检查买入操作
        if len(today_buy_stocks) > 0:  # 确保今天有需要买入的股票
            # 计算需要买入股票的权重（根据模型打分进行归一）
            today_stock_weights_sum = sum([i.get("label_pred", 0) for i in today_buy_stocks.values()])
            today_stock_weights = {k: v.get("label_pred", 0) / today_stock_weights_sum for k, v in today_buy_stocks.items()}
            for stock_code in today_buy_stocks.keys():
                data = self.getdatabyname(stock_code)
                # print(f"symbol: {data._name}, close: {data.close[0]}, high: {data.high[0]}, low: {data.low[0]}")
                position = self.getpositionbyname(stock_code)
                # 1. 权重金额：根据当前股票的权重 & 今日可用现金来计算当前股票的可用金额
                avaiable_cash_weighted = today_avaiable_cash * today_stock_weights.get(stock_code, 0)
                # 2. 头寸限制金额：所有股票的规模不能超过总金额的X%
                avaiable_cash_proportion = self.broker.get_value() * self.params.max_position_proportion
                # 3. 剩余可用金额：已有持仓的情况下，可用金额 = 头寸规模金额 - 当前占用金额
                avaiable_cash_remain = avaiable_cash_proportion - self.broker.get_value(datas=[data])
                # 4. 计算最终可用资金 = min（权重金额、头寸限制金额、剩余可用金额）
                avaiable_cash = min(avaiable_cash_weighted, avaiable_cash_proportion, avaiable_cash_remain)
                # 5. 买入执行
                buy_condition_1 = avaiable_cash > self.params.min_buy_cash
                buy_condition_2 = self.atr[data][0] > 0
                if buy_condition_1 and buy_condition_2:  # 确保开仓金额不小于条件限定
                    # todo 计算size
                    base_size = int(avaiable_cash / data.close[0])  # 计算当前可用资金下的买入Size
                    atr_size = int((avaiable_cash * self.params.atr_risk) / self.atr[data][0])  # 考虑风险控制后的买入Size
                    final_size = round(min(base_size, atr_size) / 100.0) * 100
                    if final_size > 0:
                        # print(f"symbol: {data._name}, today_atr:{self.atr[data][0]}, base_size: {base_size}, atr_size: {atr_size}, final_size: {final_size}")
                        self.buy(data=data, size=final_size, exectype=bt.Order.Market)  # 最终的买入Size = min（base_size, atr_size）
                        # 更新信息
                        self.trailing_stop_loss[stock_code] = data.low[0] - self.params.init_trailing_stop_loss_factor * self.atr[data][0]  # 初始化跟踪止损线
                        self.holding_period[stock_code] = 1  # 初始化持仓天数

        # 4. 更新其他所有持仓的持仓周期+=1
        for k in list(self.holding_period.keys()):
            self.holding_period[k] += 1
