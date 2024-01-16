import os
import json
import datetime


def save_backtest_result(save_path, backtest_profile, cerebro):
    # 用当前时间戳构建一个唯一的文件名
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    savepath_ts = f"{save_path}/{timestamp}/"
    filename_prefix = f"{savepath_ts}/backtest"

    # 保存路径检测
    if not os.path.exists(savepath_ts):
        os.makedirs(savepath_ts)

    # 保存本次回测相关数据
    with open(f"{filename_prefix}_profile.json", "w") as f:
        json.dump(backtest_profile, f, indent=4, ensure_ascii=False)

    # 保存图表（如果有的话）
    figs = cerebro.plot(style="candlestick")  # 使用蜡烛图风格，可依据需要选择其他风格
    for ind_1, fig in enumerate(figs):
        for ind_2, ax in enumerate(fig):
            ax.savefig(f"{filename_prefix}_chart_{ind_1}_{ind_2}.png")  # 保存图表为PNG文件
