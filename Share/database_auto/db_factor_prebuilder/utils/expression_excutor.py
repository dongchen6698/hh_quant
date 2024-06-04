import warnings

warnings.filterwarnings("ignore")

import pandas as pd
import numpy as np
import re
from scipy.stats import linregress


class AlphaBaseOperations:
    # ------------------------------------------
    @staticmethod
    def rank(series):
        return series.rank(pct=True)

    @staticmethod
    def log(series):
        return np.log(series)

    @staticmethod
    def sign(series):
        return np.sign(series)

    @staticmethod
    def abs(series):
        return np.abs(series)

    # ------------------------------------------
    @staticmethod
    def min(series1, series2):
        return np.minimum(series1, series2)

    @staticmethod
    def max(series1, series2):
        return np.maximum(series1, series2)

    # ------------------------------------------
    @staticmethod
    def shift(series, periods):
        return series.shift(periods)

    @staticmethod
    def diff(series, periods):
        return series.diff(periods)

    # ------------------------------------------
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
    def tsargmax(series, window):
        return series.rolling(window=window).apply(lambda x: np.argmax(x), raw=True)

    @staticmethod
    def tsargmin(series, window):
        return series.rolling(window=window).apply(lambda x: np.argmin(x), raw=True)

    @staticmethod
    def tsrank(series, window):
        return series.rolling(window=window).apply(lambda x: x.rank(pct=True).iloc[-1], raw=False)

    @staticmethod
    def idxmax(series, window):
        return series.rolling(window=window).apply(lambda x: (window - 1) - np.argmax(x), raw=True)

    @staticmethod
    def highday(series, window):
        return series.rolling(window=window).apply(lambda x: (window - 1) - np.argmax(x), raw=True)

    @staticmethod
    def idxmin(series, window):
        return series.rolling(window=window).apply(lambda x: (window - 1) - np.argmin(x), raw=True)

    @staticmethod
    def lowday(series, window):
        return series.rolling(window=window).apply(lambda x: (window - 1) - np.argmax(x), raw=True)

    # ------------------------------------------
    @staticmethod
    def correlation(series1, series2, window):
        return series1.rolling(window=window).corr(series2)

    @staticmethod
    def covariance(series1, series2, window):
        return series1.rolling(window=window).cov(series2)

    # ------------------------------------------
    @staticmethod
    def where(condition, true_series, false_series):
        return pd.Series(np.where(condition, true_series, false_series), index=condition.index)

    @staticmethod
    def quantile(series, window, quantile):
        return series.rolling(window=window).quantile(quantile)

    @staticmethod
    def clip(series, min_value, max_value):
        return np.clip(series, min_value, max_value)

    @staticmethod
    def slope(series, window):
        def linear_regression_slope(y_values):
            x_values = np.arange(len(y_values))
            slope, intercept, r_value, p_value, std_err = linregress(x_values, y_values)
            return slope

        return series.rolling(window=window).apply(linear_regression_slope, raw=True)

    @staticmethod
    def rsquare(series, window):
        def calculate_rsquare(y_values):
            x_values = np.arange(len(y_values))
            slope, intercept, r_value, p_value, std_err = linregress(x_values, y_values)
            return r_value**2

        return series.rolling(window=window).apply(calculate_rsquare, raw=True)

    @staticmethod
    def resi(series, window):
        def calculate_residuals(y_values):
            x_values = np.arange(len(y_values))
            slope, intercept, r_value, p_value, std_err = linregress(x_values, y_values)
            line = slope * x_values + intercept
            return y_values - line

        return series.rolling(window=window).apply(lambda y: calculate_residuals(y)[-1], raw=True)

    @staticmethod
    def signedpower(series, power):
        return np.sign(series) * np.abs(series) ** power

    @staticmethod
    def decaylinear(series, window):
        weights = np.arange(1, window + 1)
        return series.rolling(window=window).apply(lambda x: np.dot(x, weights) / np.sum(weights), raw=True)

    @staticmethod
    def sma(series, window, weight=1):
        weights = np.full(window, weight)
        return series.rolling(window=window).apply(lambda x: np.dot(x, weights) / np.sum(weights), raw=True)

    @staticmethod
    def wma(series, window):
        weights = np.power(0.9, np.arange(window)[::-1])
        return series.rolling(window=window).apply(lambda x: np.dot(x, weights) / np.sum(weights), raw=True)

    @staticmethod
    def count(condition_series, window):
        # 对符合条件的项进行计数
        return condition_series.rolling(window=window).sum()

    # (以下是不太确定的算子函数)------------------------------------------
    @staticmethod
    def scale(series, factor=1):
        sum_inv = factor / series.sum()
        return series * sum_inv

    @staticmethod
    def product(series, window):
        return series.rolling(window=window).apply(np.prod, raw=True)

    @staticmethod
    def sequence(n):
        return np.arange(1, n + 1)

    @staticmethod
    def regbeta(series, window):
        # 定义计算beta的函数，使用线性回归
        def calculate_beta(x):
            y = x
            x = np.arange(1, len(x) + 1)  # 生成时间序列
            slope, intercept, r_value, p_value, std_err = linregress(x, y)
            return slope

        return series.rolling(window=window).apply(calculate_beta, raw=True)


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
