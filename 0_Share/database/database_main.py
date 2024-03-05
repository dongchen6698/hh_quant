import os
import json
import sqlite3
import database_config as config
from downloader.downloader_base import DownloaderBase
from uploader.uploader_akshare import AkShareUploader
from uploader.uploader_factor import FactorUploader
from uploader.factor.expression_excutor import AlphaExpressionExcutor


def init_database():
    # 检测数据库状态
    if not os.path.exists(config.DATABASE_PATH):
        # 如果数据库文件不存在，SQLite将会创建一个
        conn = sqlite3.connect(config.DATABASE_PATH)
        print(f"数据库 {config.DATABASE_PATH} 创建成功。")
        conn.close()
    else:
        print(f"数据库 {config.DATABASE_PATH} 已经存在。")


def init_database_schema():
    conn = sqlite3.connect(config.DATABASE_PATH)
    print(f"数据库 {config.DATABASE_PATH} 连接成功。")
    # 创建一个cursor对象来帮助执行SQL语句
    cursor = conn.cursor()
    # 读取SQL模式文件
    with open(config.DATABASE_SCHEMA_PATH, "r") as f:
        create_table_sqls = f.read().split(";")  # 拆分每一个数据表的建表逻辑
        for create_table_sql in create_table_sqls:
            try:
                cursor.execute(create_table_sql)
            except Exception as e:
                print(e)
    # 提交事务
    conn.commit()
    # 关闭cursor和连接
    cursor.close()
    conn.close()
    print(f"数据库和表已经从文件 {config.DATABASE_SCHEMA_PATH} 创建于 {config.DATABASE_PATH}")


def init_database_data(start_date="20000101", end_date="20231231"):
    conn = sqlite3.connect(config.DATABASE_PATH)
    # 初始化downloader
    uploader = AkShareUploader(db_conn=conn, start_date=start_date, end_date=end_date)
    # 开始下载数据
    # uploader._upload_stock_trade_date(table_name=config.TABLE_STOCK_TRADE_DATA_INFO)  # 交易日历数据
    # uploader._upload_stock_base_info(table_name=config.TABLE_STOCK_BASE_INFO)  # 股票代码列表
    # uploader._upload_stock_history_info(table_name=config.TABLE_STOCK_HISTORY_INFO)  # 个股历史数据
    # uploader._upload_stock_individual_info(table_name=config.TABLE_STOCK_INDIVIDUAL_INFO)  # 个股基础数据
    uploader._upload_stock_indicator_info(table_name=config.TABLE_STOCK_INDICATOR_INFO)  # 个股指标信息
    # uploader._upload_index_base_info(table_name=config.TABLE_INDEX_BASE_INFO)  # 指数代码列表
    # uploader._upload_index_history_info(table_name=config.TABLE_INDEX_HISTORY_INFO)  # 指数历史数据
    # --------------------------------------------------------------------------------------------------------------
    # uploader._upload_stock_event_info(table_name=config.TABLE_STOCK_EVENT_INFO)
    # 关闭连接
    conn.close()


def init_factor_data(start_date="20000101", end_date="20231231"):
    conn = sqlite3.connect(config.DATABASE_PATH)
    # 初始化基础信息
    downloader = DownloaderBase(db_conn=conn, db_config=config)
    uploader = FactorUploader(db_conn=conn, db_downloader=downloader, start_date=start_date, end_date=end_date)
    exp_excutor = AlphaExpressionExcutor()
    # 开始构建Factor数据
    uploader._upload_date_factor(table_name=config.TABLE_STOCK_FACTOR_DATE_INFO)
    uploader._upload_qlib_factor(table_name=config.TABLE_STOCK_FACTOR_QLIB_INFO, exp_excutor=exp_excutor)
    # 关闭连接
    conn.close()


if __name__ == "__main__":
    online_update = False
    # 初始化数据库
    init_database()
    # 初始化数据表
    init_database_schema()
    # 插入数据(首次数据从20000101 ～ 20231231)
    # init_database_data(start_date="20000101", end_date="20231231")
    # 构建特征数据
    init_factor_data(start_date="20000101", end_date="20231231")
