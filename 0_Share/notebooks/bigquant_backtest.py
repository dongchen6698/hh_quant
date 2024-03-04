# 显式导入 BigQuant 相关 SDK 模块
from bigdatasource.api import DataSource
from bigdata.api.datareader import D
from biglearning.api import M
from biglearning.api import tools as T
from biglearning.module2.common.data import Outputs

import pandas as pd
import numpy as np
import math
import warnings
import datetime

from zipline.finance.commission import PerOrder
from zipline.api import get_open_orders
from zipline.api import symbol

from bigtrader.sdk import *
from bigtrader.utils.my_collections import NumPyDeque
from bigtrader.constant import OrderType
from bigtrader.constant import Direction


# @param(id="m2", name="run")
# Python 代码入口函数，input_1/2/3 对应三个输入端，data_1/2/3 对应三个输出端
def m2_run_bigquant_run(input_1, input_2, input_3):
    instrument_dict = {i.split(".")[0]: i for i in input_1.read().get("instruments")}
    df = pd.read_csv("./pred_result.csv")
    df["instrument"] = df["instrument"].map(lambda x: instrument_dict[str(x)])
    df.sort_values(["date", "pred"], inplace=True, ascending=[True, False])
    data_1 = input_1
    data_2 = DataSource.write_pickle(df)
    return Outputs(data_1=data_1, data_2=data_2, data_3=None)


# @param(id="m2", name="post_run")
# 后处理函数，可选。输入是主函数的输出，可以在这里对数据做处理，或者返回更友好的outputs数据格式。此函数输出不会被缓存。
def m2_post_run_bigquant_run(outputs):
    return outputs


# @param(id="m3", name="initialize")
# 回测引擎：初始化函数，只执行一次
def m3_initialize_bigquant_run(context):
    # 加载预测数据
    context.ranker_prediction = context.options["data"].read_df()
    # 系统已经设置了默认的交易手续费和滑点，要修改手续费可使用如下函数
    context.set_commission(PerOrder(buy_cost=0.0003, sell_cost=0.0013, min_cost=5))
    # 预测数据，通过options传入进来，使用 read_df 函数，加载到内存 (DataFrame)
    # 设置买入的股票数量，这里买入预测股票列表排名靠前的5只
    stock_count = 5
    # 每只的股票的权重，如下的权重分配会使得靠前的股票分配多一点的资金，[0.339160, 0.213986, 0.169580, ..]
    context.stock_weights = T.norm([1 / math.log(i + 2) for i in range(0, stock_count)])
    # 设置每只股票占用的最大资金比例
    context.max_cash_per_instrument = 0.2
    context.hold_days = 5


# @param(id="m3", name="handle_data")
# 回测引擎：每日数据处理函数，每天执行一次
def m3_handle_data_bigquant_run(context, data):
    # 按日期过滤得到今日的预测数据
    ranker_prediction = context.ranker_prediction[context.ranker_prediction.date == data.current_dt.strftime("%Y-%m-%d")]

    # 1. 资金分配
    # 平均持仓时间是hold_days，每日都将买入股票，每日预期使用 1/hold_days 的资金
    # 实际操作中，会存在一定的买入误差，所以在前hold_days天，等量使用资金；之后，尽量使用剩余资金（这里设置最多用等量的1.5倍）
    is_staging = context.trading_day_index < context.hold_days  # 是否在建仓期间（前 hold_days 天）
    cash_avg = context.portfolio.portfolio_value / context.hold_days
    cash_for_buy = min(context.portfolio.cash, (1 if is_staging else 1.5) * cash_avg)
    cash_for_sell = cash_avg - (context.portfolio.cash - cash_for_buy)
    positions = {e.symbol: p.amount * p.last_sale_price for e, p in context.perf_tracker.position_tracker.positions.items()}

    # 2. 生成卖出订单：hold_days天之后才开始卖出；对持仓的股票，按StockRanker预测的排序末位淘汰
    if not is_staging and cash_for_sell > 0:
        equities = {e.symbol: e for e, p in context.perf_tracker.position_tracker.positions.items()}
        instruments = list(
            reversed(
                list(
                    ranker_prediction.instrument[
                        ranker_prediction.instrument.apply(lambda x: x in equities and not context.has_unfinished_sell_order(equities[x]))
                    ]
                )
            )
        )
        # print('rank order for sell %s' % instruments)
        for instrument in instruments:
            context.order_target(context.symbol(instrument), 0)
            cash_for_sell -= positions[instrument]
            if cash_for_sell <= 0:
                break

    # 3. 生成买入订单：按StockRanker预测的排序，买入前面的stock_count只股票
    buy_cash_weights = context.stock_weights
    buy_instruments = list(ranker_prediction.instrument[: len(buy_cash_weights)])
    max_cash_per_instrument = context.portfolio.portfolio_value * context.max_cash_per_instrument
    for i, instrument in enumerate(buy_instruments):
        cash = cash_for_buy * buy_cash_weights[i]
        if cash > max_cash_per_instrument - positions.get(instrument, 0):
            # 确保股票持仓量不会超过每次股票最大的占用资金量
            cash = max_cash_per_instrument - positions.get(instrument, 0)
        if cash > 0:
            context.order_value(context.symbol(instrument), cash)


# @param(id="m3", name="prepare")
# 回测引擎：准备数据，只执行一次
def m3_prepare_bigquant_run(context):
    pass


# @param(id="m3", name="before_trading_start")
# 回测引擎：每个单位时间开始前调用一次，即每日开盘前调用一次。
def m3_before_trading_start_bigquant_run(context, data):
    pass


# @module(position="606,520", comment='', comment_collapsed=True)
m1 = M.instruments.v2(start_date="2020-01-01", end_date="2020-12-31", market="CN_STOCK_A", instrument_list="", max_count=0)

# @module(position="606,648", comment='', comment_collapsed=True)
m2 = M.cached.v3(input_1=m1.data, run=m2_run_bigquant_run, post_run=m2_post_run_bigquant_run, input_ports="", params="{}", output_ports="")

# @module(position="605,803", comment='', comment_collapsed=True)
m3 = M.trade.v4(
    instruments=m2.data_1,
    options_data=m2.data_2,
    start_date="2020-01-01",
    end_date="2020-12-31",
    initialize=m3_initialize_bigquant_run,
    handle_data=m3_handle_data_bigquant_run,
    prepare=m3_prepare_bigquant_run,
    before_trading_start=m3_before_trading_start_bigquant_run,
    volume_limit=0.025,
    order_price_field_buy="open",
    order_price_field_sell="close",
    capital_base=1000000,
    auto_cancel_non_tradable_orders=True,
    data_frequency="daily",
    price_type="后复权",
    product_type="股票",
    plot_charts=True,
    backtest_only=True,
    benchmark="000300.HIX",
)
