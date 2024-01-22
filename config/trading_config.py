# trading_config.py

# 定义交易模式，可以是 'backtest'、'simulation' 或者 'live'
MODE = "backtest"

# 定义回测或模拟交易的初始资金
INITIAL_CASH = 100000.0

# 定义交易佣金，表示每笔交易的百分比成本
COMMISSION_PER_TRADE = 0.001  # 0.1%

# 定义滑点大小，表示买入或卖出价格与实际成交价格的差异
SLIPPAGE = 0.05  # 0.05元

# 如果使用实盘交易，定义交易接口相关的配置，例如：
BROKER_API_PARAMS = {
    "api_key": "your_api_key",
    "api_secret": "your_api_secret",
    "endpoint": "https://api.broker.com",
}

# 回测时的数据源配置，例如：
BACKTEST_DATA_SOURCE = {
    "data_path": "path_to_your_historical_data.csv",
    "data_format": "csv",
}  # 或 'database', 'api' 等

# 模拟交易时的数据源配置，例如：
SIMULATION_DATA_SOURCE = {
    "api_key": "your_data_source_api_key",
    "endpoint": "https://api.data_source.com",
    "symbols": ["AAPL", "GOOGL", "MSFT"],
}  # 股票代码列表

# 实盘交易时的市场连接配置，例如：
LIVE_MARKET_CONNECTION = {
    "streaming_api": "https://stream.broker.com",
    "account_id": "your_account_id",
    "access_token": "your_access_token",
}

# 可以根据需要添加其它的交易相关配置...
