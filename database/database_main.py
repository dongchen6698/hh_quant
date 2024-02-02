import os
import sqlite3
import database_config as config
from database.uploader.uploader_akshare import AkShareUploader


# 数据相关配置
INIT_START_DATE = "20000101"
INIT_END_DATA = "20050101"


def init_database():
    # 检测数据库状态
    if not os.path.exists(config.DATABASE_PATH):
        # 如果数据库文件不存在，SQLite将会创建一个
        conn = sqlite3.connect(config.DATABASE_PATH)
        print(f"数据库 {config.DATABASE_PATH} 创建成功。")
        conn.close()


def init_database_schema():
    conn = sqlite3.connect(config.DATABASE_PATH)
    print(f"数据库 {config.DATABASE_PATH} 连接成功。")
    # 创建一个cursor对象来帮助执行SQL语句
    cursor = conn.cursor()
    # 读取SQL模式文件
    with open(config.DATABASE_SCHEMA_PATH, "r") as f:
        schema_sql = f.read()
    # 如果.sql文件包含多个SQL语句，确保它们以分号结束
    cursor.executescript(schema_sql)
    # 提交事务
    conn.commit()
    # 关闭cursor和连接
    cursor.close()
    conn.close()
    print(f"数据库和表已经从文件 {config.DATABASE_SCHEMA_PATH} 创建于 {config.DATABASE_PATH}")


def init_database_data(start_date, end_date):
    conn = sqlite3.connect(config.DATABASE_PATH)
    # 初始化downloader
    uploader = AkShareUploader(db_conn=conn)
    uploader._upload_stock_trade_date(table_name=config.TABLE_STOCK_TRADE_DATA_INFO)
    uploader._upload_stock_base_info(table_name=config.TABLE_STOCK_BASE_INFO)
    uploader._upload_stock_individual_info(table_name=config.TABLE_STOCK_INDIVIDUAL_INFO)
    uploader._upload_stock_history_info(table_name=config.TABLE_STOCK_HISTORY_INFO, start_date=start_date, end_date=end_date)
    uploader._upload_stock_event_info(table_name=config.TABLE_STOCK_EVENT_INFO, start_date=start_date, end_data=end_date)
    # 关闭连接
    conn.close()


if __name__ == "__main__":
    # 初始化数据库
    init_database()
    # 初始化数据表
    init_database_schema()
    # 插入数据
    init_database_data(start_date="20000101", end_date="20100101")
