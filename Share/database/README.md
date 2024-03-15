# 数据平台内容
> 数据来源：Akshare、TuShare、BaoStock、爬虫、etc

## 通用数据
- 全年交易日历信息：
    - ak.tool_trade_date_hist_sina()
- etc

## 股票数据
- 股票代码列表
    - ak.stock_info_a_code_name() # 并通过utils获取prefix
- 行情数据（前复权、后复权、不复权）: 
    - ak.stock_zh_a_daily() # 新浪接口，东财数据的复权方式由于是加减法复权，无法用于回测
- 个股基本信息
    - ak.stock_individual_info_em() # 东财个股信息，stock_code不带标识前缀
- 基本面信息
    - ak.stock_a_indicator_lg() # 乐咕乐股-A股个股市盈率、市净率和股息率指标（存在接口限制）
- etc

## 指数数据
- 指数代码列表：
    - ak.index_stock_info()
- 指数成分股信息
    - ak.index_stock_info() # 获取指数成分股
- 行情数据
    - ak.index_zh_a_hist()

## 财务数据
- 

## 行业数据
- 行业成交：
    - ak.stock_szse_sector_summary() # 股票行业月度成交信息
- 行业市盈率：
    - ak.stock_industry_pe_ratio_cninfo()

## 舆情数据
- 宏观
    - ak.news_economic_baidu() # 全球宏观事件数据
- 财经新闻
- 个股新闻
    - ak.stock_news_em() #  个股最近100条新闻，需要尽早开始收集
- 行业新闻
- etc

# 因子构建
- 价量因子
- 基本面因子
- etc