import warnings

warnings.filterwarnings("ignore")

import pandas as pd
import numpy as np
import re


class AlphaBaseOperations:
    @staticmethod
    def min(series1, series2):
        return np.minimum(series1, series2)

    @staticmethod
    def max(series1, series2):
        return np.maximum(series1, series2)

    @staticmethod
    def shift(series, period):
        return series.shift(period)

    @staticmethod
    def rank(series):
        return series.rank(pct=True)

    @staticmethod
    def log(series):
        return np.log(series)

    @staticmethod
    def delta(series, period):
        return series.diff(period)

    @staticmethod
    def sign(series):
        return np.sign(series)

    @staticmethod
    def abs(series):
        return np.abs(series)

    @staticmethod
    def corr(series1, series2, window):
        return series1.rolling(window=window).corr(series2)

    @staticmethod
    def std(series, window):
        return series.rolling(window=window).std()

    @staticmethod
    def mean(series, window):
        return series.rolling(window=window).mean()

    @staticmethod
    def sum(series, window):
        return series.rolling(window=window).sum()

    @staticmethod
    def tsmax(series, window):
        return series.rolling(window=window).max()

    @staticmethod
    def tsmin(series, window):
        return series.rolling(window=window).min()

    @staticmethod
    def quantile(series, window, quantile):
        return series.rolling(window=window).quantile(quantile)

    @staticmethod
    def idxmax(series, window):
        return series.rolling(window=window).apply(lambda x: (window - 1) - x.argmax(), raw=True)

    @staticmethod
    def idxmin(series, window):
        return series.rolling(window=window).apply(lambda x: (window - 1) - x.argmin(), raw=True)

    @staticmethod
    def slope(series, window):
        # 计算每个窗口上的斜率
        def linear_regression_slope(y):
            x = np.arange(len(y))
            A = np.vstack([x, np.ones(len(x))]).T
            m, c = np.linalg.lstsq(A, y, rcond=None)[0]
            return m

        return series.rolling(window=window).apply(linear_regression_slope, raw=True)

    @staticmethod
    def rsquare(series, window):
        # 对每个窗口计算R平方值
        def compute_rsquare(y):
            x = np.arange(len(y))
            A = np.vstack([x, np.ones(len(x))]).T
            m, c = np.linalg.lstsq(A, y, rcond=None)[0]
            y_fit = m * x + c  # 线性拟合值
            ss_res = np.sum((y - y_fit) ** 2)  # 残差平方和
            ss_tot = np.sum((y - np.mean(y)) ** 2)  # 总平方和
            r_squared = 1 - (ss_res / ss_tot)  # R平方计算公式
            return r_squared

        return series.rolling(window=window).apply(compute_rsquare, raw=True)

    @staticmethod
    def resi(series, window):
        # 对每个窗口计算残差
        def compute_residuals(y):
            x = np.arange(len(y))
            A = np.vstack([x, np.ones(len(x))]).T
            m, c = np.linalg.lstsq(A, y, rcond=None)[0]
            y_fit = m * x + c  # 线性拟合值
            residuals = y - y_fit  # 残差
            return residuals[-1]  # 返回窗口中最后一个残差值

        return series.rolling(window=window).apply(compute_residuals, raw=True)

    @staticmethod
    def tsrank(series, window):
        # 计算滚动排名
        return series.rolling(window=window).apply(lambda x: x.rank().iloc[-1], raw=False)

    @staticmethod
    def where(condition, true_series, false_series):
        return pd.Series(np.where(condition, true_series, false_series), index=condition.index)

    @staticmethod
    def clip(series, min_value, max_value):
        return np.clip(series, min_value, max_value)

    @staticmethod
    def all_quantile(series, percent):
        return np.nanquantile(series, percent)

    @staticmethod
    def sma(series, window, weight):
        weights = np.arange(1, weight + 1)[::-1]  # 生成权重数组，例如当weight=2时，weights为[2, 1]
        return series.rolling(window=window).apply(lambda x: np.dot(weights[-len(x) :], x[-len(weights) :]) / weights[-len(x) :].sum(), raw=False)

    @staticmethod
    def wma(series, window):
        weights = np.arange(1, window + 1)  # 生成权重数组，例如当window=3时，weights为[1, 2, 3]
        return series.rolling(window=window).apply(lambda x: np.dot(weights, x[-window:]) / weights.sum(), raw=False)

    @staticmethod
    def decaylinear(series, window):
        # 生成线性衰减的权重，最旧的数据点权重为1，最新的为window
        weights = np.arange(1, window + 1)
        # 计算加权移动平均，每个窗口应用权重并取平均
        return series.rolling(window=window).apply(lambda x: np.dot(x, weights) / weights.sum(), raw=False)


class AlphaExpressionExcutor:
    def __init__(self):
        self.ops = AlphaBaseOperations()
        self.local_ops = {func.lower(): getattr(self.ops, func) for func in dir(self.ops) if callable(getattr(self.ops, func)) and not func.startswith("__")}

    def expression_regex(self, expression):
        expression = re.sub(r"\^", "**", expression)  # 指数替换
        expression = re.sub(r"(?<!<)(?<!>)\=", "==", expression)  # 将单独的等号替换为双等号
        expression = re.sub(r"\b[A-Za-z_][A-Za-z0-9_]*\b", lambda match: match.group().lower(), expression)  # 全部小写替换
        return expression

    def excute(self, df, expression):
        # 创建包含列名和方法的本地字典
        self.local_ops.update({col_name.lower(): df[col_name] for col_name in df.columns})  # 通过字典的方式映射dataframe中的column
        # 表达式修正
        expression = self.expression_regex(expression)
        return eval(expression, {"np": np, "nan": np.nan}, self.local_ops)
