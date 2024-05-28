# 本示例运行于python3.6及以上版本
from gmtrade.api import *

TOKEN = "1b2af86543ef183f643910386e92435624453070"
ACCOUNT = "6f6e4db8-1cb2-11ef-bab8-00163e022aa6"

# token身份认证，掘金登录后可在仿真交易官网获取
set_token(TOKEN)

# 示例中为掘金官方仿真服务地址，如接入掘金终端，则填空
set_endpoint("api.myquant.cn:9000")

# 登录账户，账户ID由登录并申请仿真账户后，可复制获取；account_alias为账号别名，选填
a1 = account(account_id=ACCOUNT, account_alias="")
login(a1)  # 注意，可以输入账户也可以输入账户组成的list


# 回报到达时触发
def on_execution_report(rpt):
    print(f"exec_rpt_count={rpt}")


# 委托状态变化时触发
def on_order_status(order):
    print(f"order_stats_count={order}")


# 交易服务连接成功后触发
def on_trade_data_connected():
    print("已连接交易服务.................")


# 交易服务断开后触发
def on_trade_data_disconnected():
    print("已断开交易服务.................")


# 回报到达时触发
def on_account_status(account_status):
    print(f"on_account_status status={account_status}")


if __name__ == "__main__":
    # start函数用于启动回调事件接收，非必要；事件函数为非阻塞函数，如需要同步执行需自行阻塞
    # filename=__file__用于指定当前运行的文件，如需要指定其他文件filename=‘xxx’
    status = start(filename=__file__)
    if status == 0:
        print("连接交易服务成功.................")
    else:
        print("接交易服务失败.................")
        stop()

    # 开始交易业务
    order_volume(
        symbol="SHSE.600000",
        volume=10,
        side=OrderSide_Buy,
        order_type=OrderType_Market,
        position_effect=PositionEffect_Open,
    )

    # 保持进程不退出，否则回调不再生效
    info = input("输入任字符退出")
