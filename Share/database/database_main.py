import os
import json
import sqlite3
import database_config as config
from datetime import datetime, timedelta
from downloader.downloader_base import DownloaderBase
from uploader import AkShareUploader, BaoStockUploader


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
            # print(create_table_sql)
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
    # 初始化uploader
    downloader = DownloaderBase(db_conn=conn, db_config=config)
    uploader_ak = AkShareUploader(db_conn=conn, start_date=start_date, end_date=end_date)
    uploader_bs = BaoStockUploader(db_conn=conn, db_downloader=downloader, start_date=start_date, end_date=end_date)
    # 开始下载数据(Akshare)
    uploader_ak._upload_stock_trade_date(table_name=config.TABLE_STOCK_TRADE_DATA_INFO)  # 交易日历数据
    # uploader_ak._upload_stock_base_info(table_name=config.TABLE_STOCK_BASE_INFO)  # 股票代码列表
    # uploader_ak._upload_stock_individual_info(table_name=config.TABLE_STOCK_INDIVIDUAL_INFO)  # 个股基础数据
    # # 开始下载数据(Baostock)
    uploader_bs._bs_login()  # 登陆系统
    # uploader_bs._upload_stock_history_info(table_name=config.TABLE_STOCK_HISTORY_INFO)  # 个股历史数据
    # uploader_bs._upload_stock_indicator_info(table_name=config.TABLE_STOCK_INDICATOR_INFO)  # 个股指标信息
    uploader_bs._upload_index_history_info(table_name=config.TABLE_INDEX_HISTORY_INFO)  # 指数历史数据
    uploader_bs._bs_logout()  # 登出系统
    # --------------------------------------------------------------------------------------------------------------
    # uploader._upload_stock_event_info(table_name=config.TABLE_STOCK_EVENT_INFO)
    # 关闭连接
    conn.close()


if __name__ == "__main__":
    # import argparse
    # parser = argparse.ArgumentParser(description='argparse testing')
    # parser.add_argument('--update','-n',type=str, default = "bk",required=True,help="a programmer's name")
    # args = parser.parse_args()

    online_update = True
    # 初始化数据库
    init_database()
    # 初始化数据表
    init_database_schema()
    if not online_update:
        # 插入数据(首次数据从20000101 ～ 20231231)
        init_database_data(start_date="20000101", end_date="20231231")
    else:
        # 还需要继续优化
        db_conn = sqlite3.connect(config.DATABASE_PATH)
        db_downloader = DownloaderBase(db_conn=db_conn, db_config=config)
        last_date = datetime.strptime(db_downloader._download_stock_trade_date()["datetime"].max(), "%Y-%m-%d")
        update_start_date = datetime.strftime(last_date + timedelta(days=1), "%Y%m%d")
        update_end_date = datetime.strftime(datetime.now(), "%Y%m%d")
        # 更新数据
        print(f"Update start date: {update_start_date}, Update end date: {update_end_date}")
        init_database_data(start_date=update_start_date, end_date=update_end_date)
