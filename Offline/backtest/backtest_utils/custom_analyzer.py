import backtrader as bt
import numpy as np
import math
from scipy.stats import linregress


class CustomAnalyzer(bt.Analyzer):
    """
    自定义分析器，计算策略收益相关指标。
    """

    def create_analysis(self):
        # 初始化存储分析结果的字典
        self.rets = {
            "盈利次数": 0,
            "亏损次数": 0,
        }
        self.val_start = self.strategy.broker.get_cash()  # 初始资金
        self.val_end = None  # 结束资金

        # 初始化用于计算的数据
        self.equity_curve = []  # 记录每日净值
        self.returns = []  # 日收益率
        self.benchmark_curve = []  # 基准每日净值
        self.benchmark_returns = []  # 基准日收益率
        self.excess_returns = []  # 超额日收益率
        self.win_trades = []  # 盈利交易的盈亏
        self.loss_trades = []  # 亏损交易的盈亏

    def notify_trade(self, trade):
        if trade.isclosed:
            # 统计盈利次数和亏损次数
            if trade.pnl > 0:
                self.win_trades.append(trade.pnl)
                self.rets["盈利次数"] += 1
            elif trade.pnl < 0:
                self.loss_trades.append(trade.pnl)
                self.rets["亏损次数"] += 1

    def notify_cashvalue(self, cash, value):
        self.val_end = value  # 更新结束资金
        # 确保 value 是有效的数值
        if value is not None and not (math.isnan(value) or math.isinf(value)):
            self.equity_curve.append(value)
            # 只有在有前一个值可比较时才计算收益
            if len(self.equity_curve) > 1:
                self.returns.append(self.equity_curve[-1] / self.equity_curve[-2] - 1)

        # 如果有基准数据，则同时更新
        if hasattr(self.strategy, "benchmark") and len(self.strategy.benchmark):
            # 确保基准数据真的存在且有效
            benchmark_value = self.strategy.benchmark.close[0]
            if benchmark_value is not None and not (math.isnan(benchmark_value) or math.isinf(benchmark_value)):
                self.benchmark_curve.append(benchmark_value)
                # 只有在有前一个值可比较时才计算基准收益
                if len(self.benchmark_curve) > 1:
                    self.benchmark_returns.append(self.benchmark_curve[-1] / self.benchmark_curve[-2] - 1)
                    # 确保策略收益也已更新，才计算超额收益
                    if len(self.returns) == len(self.benchmark_returns):
                        self.excess_returns.append(self.returns[-1] - self.benchmark_returns[-1])
                    else:
                        # 如果长度不匹配，记录一个错误 或 抛出异常
                        print("Error: Returns and benchmark returns list lengths do not match")

    def stop(self):
        # 在结束时调用每个计算方法
        self.calculate_strategy_returns()  # 计算策略整体收益
        self.calculate_annualized_returns()  # 计算策略年化收益
        self.calculate_benchmark_returns()  # 计算基准收益
        self.calculate_benchmark_annualized_returns()  # 计算基准年化收益
        self.calculate_excess_returns()  # 计算策略相对于基准的超额收益
        self.calculate_beta_alpha()  # 计算贝塔系数和阿尔法值，评估策略相对于市场的风险和表现
        self.calculate_win_ratio()  # 计算策略的胜率，即盈利交易占比
        self.calculate_max_drawdown()  # 计算最大回撤及其持续时间，评估策略的潜在风险
        self.calculate_profit_loss_ratio()  # 计算盈亏比，衡量平均盈利交易相对于平均亏损交易的大小
        self.calculate_sharpe_ratio()  # 计算夏普比率，评估策略的风险调整后收益
        self.calculate_sortino_ratio()  # 计算索提诺比率，专注于策略的下行风险
        self.calculate_average_excess_return()  # 计算日均超额收益，衡量策略相对于基准的平均每日表现
        self.calculate_excess_sharpe_ratio()  # 计算超额收益的夏普比率，评估策略超额收益的风险调整后表现
        self.calculate_daily_win_ratio()  # 计算日胜率，即每日盈利交易的比例
        self.calculate_volatility()  # 计算策略和基准的波动率，衡量价格波动的幅度

    def calculate_strategy_returns(self):
        """计算策略收益
        策略收益 = (结束资金 / 初始资金) - 1
        表示策略在整个交易期间的总收益率。
        """
        self.rets["策略收益"] = self.val_end / self.val_start - 1

    def calculate_annualized_returns(self):
        """计算策略年化收益
        年化收益 = ((策略收益 + 1) ^ (252 / 交易天数)) - 1
        假设一年有252个交易日，计算策略如果持续一年所能获得的预期收益率。
        """
        days = len(self.equity_curve)
        if days > 0:
            self.rets["策略年化收益"] = (self.rets["策略收益"] + 1) ** (252 / days) - 1
        else:
            self.rets["策略年化收益"] = 0

    def calculate_benchmark_returns(self):
        """计算基准收益
        基准收益 = (基准结束净值 / 基准开始净值) - 1
        表示选定的市场基准在同一交易期间的收益率，用于与策略收益进行比较。
        """
        if self.benchmark_curve:
            self.rets["基准收益"] = self.benchmark_curve[-1] / self.benchmark_curve[0] - 1
        else:
            self.rets["基准收益"] = 0

    def calculate_benchmark_annualized_returns(self):
        """计算基准年化收益
        基准年化收益 = ((基准收益 + 1) ^ (252 / 交易天数)) - 1
        假设一年有252个交易日，计算基准如果持续一年所能获得的预期收益率。
        """
        days = len(self.benchmark_curve)
        if days > 0:
            self.rets["基准年化收益"] = (self.rets["基准收益"] + 1) ** (252 / days) - 1
        else:
            self.rets["基准年化收益"] = 0

    def calculate_excess_returns(self):
        """计算超额收益
        超额收益 = 策略收益 - 基准收益
        表示策略相对于基准的超额收益情况。
        """
        self.rets["超额收益"] = self.rets["策略收益"] - self.rets["基准收益"]

    def calculate_beta_alpha(self):
        """计算贝塔和阿尔法
        贝塔：衡量策略相对于基准市场波动的敏感性。
        阿尔法：衡量策略相对于市场预期收益的超额表现。
        使用线性回归的斜率作为贝塔，截距作为阿尔法。
        """
        if len(self.benchmark_returns) > 1 and len(self.returns) > 1:
            slope, intercept, _, _, _ = linregress(self.benchmark_returns, self.returns)
            self.rets["贝塔"] = slope
            self.rets["阿尔法"] = intercept

    def calculate_win_ratio(self):
        """计算胜率
        胜率 = 盈利次数 / 总交易次数
        表示策略中盈利交易的比例，可以用来衡量策略的成功率。
        """
        total_trades = self.rets["盈利次数"] + self.rets["亏损次数"]
        self.rets["胜率"] = self.rets["盈利次数"] / total_trades if total_trades > 0 else 0

    def calculate_max_drawdown(self):
        """计算最大回撤及其持续时间
        最大回撤：从峰值到谷底的最大损失。
        最大回撤区间：最大回撤发生的时间长度。
        这两项指标共同评估策略的潜在风险和资金的保持期间。
        """
        drawdown_analysis = self.strategy.analyzers.getbyname("drawdown").get_analysis()
        self.rets["最大回撤"] = drawdown_analysis.max.drawdown
        self.rets["最大回撤区间"] = drawdown_analysis.len

    def calculate_profit_loss_ratio(self):
        """计算盈亏比
        盈亏比 = 平均盈利交易额 / 平均亏损交易额
        衡量策略中平均每笔盈利交易相对于平均每笔亏损交易的比率，高比值通常更受青睐。
        """
        if self.loss_trades:
            average_win = sum(self.win_trades) / len(self.win_trades)
            average_loss = sum(self.loss_trades) / len(self.loss_trades)
            self.rets["盈亏比"] = abs(average_win / average_loss)

    def calculate_sharpe_ratio(self):
        """计算夏普比率
        夏普比率 = (策略平均日收益率 - 无风险利率) / 策略日收益率标准差 * sqrt(252)
        评估策略的风险调整后收益，衡量单位风险所带来的超额收益。这里假设无风险利率为0。
        """
        if np.std(self.returns) != 0:
            self.rets["夏普比率"] = np.mean(self.returns) / np.std(self.returns) * np.sqrt(252)

    def calculate_sortino_ratio(self):
        """计算索提诺比率
        索提诺比率 = (策略平均日收益率 - 无风险利率) / 下行风险的标准差 * sqrt(252)
        与夏普比率类似，但只考虑下行风险，更关注策略的潜在亏损。
        """
        downside_returns = [x for x in self.returns if x < 0]
        if downside_returns and np.std(downside_returns) != 0:
            self.rets["索提诺比率"] = np.mean(self.returns) / np.std(downside_returns) * np.sqrt(252)

    def calculate_average_excess_return(self):
        """计算日均超额收益
        日均超额收益 = 超额日收益率的平均值
        衡量策略相对于基准的平均每日超额表现。
        """
        self.rets["日均超额收益"] = np.mean(self.excess_returns) if self.excess_returns else 0

    def calculate_excess_sharpe_ratio(self):
        """计算超额收益的夏普比率
        超额收益夏普比率 = 超额日收益率的平均值 / 超额日收益率的标准差 * sqrt(252)
        评估策略超额收益的风险调整后表现。
        """
        if np.std(self.excess_returns) != 0:
            self.rets["超额收益夏普比率"] = np.mean(self.excess_returns) / np.std(self.excess_returns) * np.sqrt(252)

    def calculate_daily_win_ratio(self):
        """计算日胜率
        日胜率 = 每日盈利次数 / 总交易天数
        表示策略每个交易日盈利的概率，反映了策略日常表现的稳定性。
        """
        wins = len([x for x in self.returns if x > 0])
        self.rets["日胜率"] = wins / len(self.returns) if self.returns else 0

    def calculate_volatility(self):
        """计算波动率
        策略波动率 = 策略日收益率的标准差 * sqrt(252)
        基准波动率 = 基准日收益率的标准差 * sqrt(252)
        衡量策略和基准的价格波动幅度。波动率越高，表示价格波动越大，风险可能也越高。
        """
        self.rets["策略波动率"] = np.std(self.returns) * np.sqrt(252) if self.returns else 0
        self.rets["基准波动率"] = np.std(self.benchmark_returns) * np.sqrt(252) if self.benchmark_returns else 0

    def get_analysis(self):
        """获取分析结果"""
        return self.rets

    def get_strategy_returns(self):
        return self.returns

    def get_benchmark_returns(self):
        return self.benchmark_returns
