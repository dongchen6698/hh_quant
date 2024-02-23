import warnings

warnings.filterwarnings("ignore")

import pandas as pd
import numpy as np
import re


class AlphaBaseOperations:
    # alpha158相关operations
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


class AlphaFactorGenerator:
    def get_alpha_expression(self):
        fields, names = [], []

        # = KBar ==============================================================================
        fields += [
            "(close-open)/open",
            "(high-low)/open",
            "(close-open)/(high-low+1e-12)",
            "(high-max(open,close))/open",
            "(high-max(open,close))/(high-low+1e-12)",
            "(min(open,close)-low)/open",
            "(min(open,close)-low)/(high-low+1e-12)",
            "(2*close-high-low)/open",
            "(2*close-high-low)/(high-low+1e-12)",
        ]
        names += [
            "KMID",
            "KLEN",
            "KMID2",
            "KUP",
            "KUP2",
            "KLOW",
            "KLOW2",
            "KSFT",
            "KSFT2",
        ]
        # = Price ==============================================================================
        feature = ["open", "high", "low", "close", "vwap"]
        windows = range(5)
        for field in feature:
            field = field.lower()
            fields += [f"shift({field},{d})/close" if d != 0 else f"{field}/close" for d in windows]
            names += [field.upper() + str(d) for d in windows]

        # = Volume ==============================================================================
        fields += [f"shift(volume,{d})/(volume+1e-12)" if d != 0 else f"volume/(volume+1e-12)" for d in windows]
        names += ["VOLUME" + str(d) for d in windows]

        # = Rolling ==============================================================================
        # Some factor ref: https://guorn.com/static/upload/file/3/134065454575605.pdf
        windows = [5, 10, 20, 30, 60]
        # https://www.investopedia.com/terms/r/rateofchange.asp
        # Rate of change, the price change in the past d days, divided by latest close price to remove unit
        fields += [f"shift(close,{d})/close" for d in windows]
        names += [f"ROC{d}" for d in windows]

        # The max price for past d days, divided by latest close price to remove unit
        fields += [f"max(high,{d})/close" for d in windows]
        names += [f"MAX{d}" for d in windows]

        # The low price for past d days, divided by latest close price to remove unit
        fields += [f"min(low,{d})/close" for d in windows]
        names += [f"MIN{d}" for d in windows]

        # https://www.investopedia.com/ask/answers/071414/whats-difference-between-moving-average-and-weighted-moving-average.asp
        # Simple Moving Average, the simple moving average in the past d days, divided by latest close price to remove unit
        fields += [f"mean(close,{d})/close" for d in windows]
        names += [f"MA{d}" for d in windows]

        # The standard diviation of close price for the past d days, divided by latest close price to remove unit
        fields += [f"std(close,{d})/close" for d in windows]
        names += [f"STD{d}" for d in windows]

        # The rate of close price change in the past d days, divided by latest close price to remove unit
        # For example, price increase 10 dollar per day in the past d days, then Slope will be 10.
        fields += [f"slope(close,{d})/close" for d in windows]
        names += [f"BETA{d}" for d in windows]

        # The R-sqaure value of linear regression for the past d days, represent the trend linear
        fields += [f"rsquare(close,{d})" for d in windows]
        names += [f"RSQR{d}" for d in windows]

        # The redisdual for linear regression for the past d days, represent the trend linearity for past d days.
        fields += [f"resi(close,{d})/close" for d in windows]
        names += [f"RESI{d}" for d in windows]

        # The 80% quantile of past d day's close price, divided by latest close price to remove unit
        # Used with MIN and MAX
        fields += [f"quantile(close,{d},0.8)/close" for d in windows]
        names += [f"QTLU{d}" for d in windows]

        # The 20% quantile of past d day's close price, divided by latest close price to remove unit
        fields += [f"quantile(close,{d},0.2)/close" for d in windows]
        names += [f"QTLD{d}" for d in windows]

        # Get the percentile of current close price in past d day's close price.
        # Represent the current price level comparing to past N days, add additional information to moving average.
        fields += [f"tsrank(close,{d})" for d in windows]
        names += [f"TSRANK{d}" for d in windows]

        # Represent the price position between upper and lower resistent price for past d days.
        fields += [f"(close-min(low,{d}))/(max(high,{d})-min(low,{d})+1e-12)" for d in windows]
        names += [f"RSV{d}" for d in windows]

        # The number of days between current date and previous highest price date.
        # Part of Aroon Indicator https://www.investopedia.com/terms/a/aroon.asp
        # The indicator measures the time between highs and the time between lows over a time period.
        # The idea is that strong uptrends will regularly see new highs, and strong downtrends will regularly see new lows.
        fields += [f"idxmax(high,{d})/{d}" for d in windows]
        names += [f"IMAX{d}" for d in windows]

        # The number of days between current date and previous lowest price date.
        # Part of Aroon Indicator https://www.investopedia.com/terms/a/aroon.asp
        # The indicator measures the time between highs and the time between lows over a time period.
        # The idea is that strong uptrends will regularly see new highs, and strong downtrends will regularly see new lows.
        fields += [f"idxmin(low,{d})/{d}" for d in windows]
        names += [f"IMIN{d}" for d in windows]

        # The time period between previous lowest-price date occur after highest price date.
        # Large value suggest downward momemtum.
        fields += [f"(idxmax(high,{d})-idxmin(low,{d}))/{d}" for d in windows]
        names += [f"IMXD{d}" for d in windows]

        # The correlation between absolute close price and log scaled trading volume
        fields += [f"corr(close,log(volume+1),{d})" for d in windows]
        names += [f"CORR{d}" for d in windows]

        # The correlation between price change ratio and volume change ratio
        fields += [f"corr(close/shift(close,1), log(volume/shift(volume,1)+1), {d})" for d in windows]
        names += [f"CORD{d}" for d in windows]

        # The percentage of days in past d days that price go up.
        fields += [f"mean(close>shift(close,1), {d})" for d in windows]
        names += [f"CNTP{d}" for d in windows]

        # The percentage of days in past d days that price go down.
        fields += [f"mean(close<shift(close,1), {d})" for d in windows]
        names += [f"CNTN{d}" for d in windows]

        # The diff between past up day and past down day
        fields += [f"mean(close>shift(close,1), {d})-mean(close<shift(close,1), {d})" for d in windows]
        names += [f"CNTD{d}" for d in windows]

        # The total gain / the absolute total price changed
        # Similar to RSI indicator. https://www.investopedia.com/terms/r/rsi.asp
        fields += [f"sum(max(close-shift(close,1),0),{d})/(sum(abs(close-shift(close,1)), {d})+1e-12)" for d in windows]
        names += [f"SUMP{d}" for d in windows]

        # The total lose / the absolute total price changed
        # Can be derived from SUMP by SUMN = 1 - SUMP
        # Similar to RSI indicator. https://www.investopedia.com/terms/r/rsi.asp
        fields += [f"sum(max(shift(close,1)-close,0), {d})/(sum(abs(close-shift(close,1)), {d})+1e-12)" for d in windows]
        names += [f"SUMN{d}" for d in windows]

        # The diff ratio between total gain and total lose
        # Similar to RSI indicator. https://www.investopedia.com/terms/r/rsi.asp
        fields += [
            f"(sum(max(close-shift(close,1),0), {d})-sum(max(shift(close,1)-close,0), {d}))/(sum(abs(close-shift(close,1)), {d})+1e-12)" for d in windows
        ]
        names += [f"SUMD{d}" for d in windows]

        # Simple Volume Moving average: https://www.barchart.com/education/technical-indicators/volume_moving_average
        fields += [f"mean(volume,{d})/(volume+1e-12)" for d in windows]
        names += [f"VMA{d}" for d in windows]

        # The standard deviation for volume in past d days.
        fields += [f"std(volume,{d})/(volume+1e-12)" for d in windows]
        names += [f"VSTD{d}" for d in windows]

        # The volume weighted price change volatility
        fields += [f"std(abs(close/shift(close,1)-1)*volume,{d})/(mean(abs(close/shift(close,1)-1)*volume,{d})+1e-12)" for d in windows]
        names += [f"WVMA{d}" for d in windows]

        # The total volume increase / the absolute total volume changed
        fields += [f"sum(max(volume-shift(volume,1),0), {d})/(sum(abs(volume-shift(volume,1)),{d})+1e-12)" for d in windows]
        names += [f"VSUMP{d}" for d in windows]

        # The total volume increase / the absolute total volume changed
        # Can be derived from VSUMP by VSUMN = 1 - VSUMP
        fields += [f"sum(max(shift(volume, 1)-volume, 0), {d})/(sum(abs(volume-shift(volume,1)),{d})+1e-12)" for d in windows]
        names += [f"VSUMN{d}" for d in windows]

        # The diff ratio between total volume increase and total volume decrease
        # RSI indicator for volume
        fields += [
            f"(sum(max(volume-shift(volume,1),0), {d})-sum(max(shift(volume,1)-volume,0),{d}))/(sum(abs(volume-shift(volume,1)),{d})+1e-12)" for d in windows
        ]
        names += [f"VSUMD{d}" for d in windows]

        result = {}
        for field_name, field_expression in zip(names, fields):
            result[field_name] = field_expression
        return result


def calculate_alpha_expression(df, expression):
    # 创建 Alpha101Ops 类的实例
    ops = AlphaBaseOperations()
    # 创建包含列名和方法的本地字典
    local_dict = {col_name.lower(): df[col_name] for col_name in df.columns}  # 通过字典的方式映射dataframe中的column
    local_dict.update({func.lower(): getattr(ops, func) for func in dir(ops) if callable(getattr(ops, func)) and not func.startswith("__")})  # 添加算子方法

    # 表达式修正
    expression = re.sub(r"\^", "**", expression)  # 指数替换
    expression = re.sub(r"(?<!<)(?<!>)\=", "==", expression)  # 将单独的等号替换为双等号
    expression = re.sub(r"\b[A-Za-z_][A-Za-z0-9_]*\b", lambda match: match.group().lower(), expression)  # 全部小写替换
    # print(f'Updated Expression: {expression}')
    return eval(expression, {"np": np}, local_dict)
