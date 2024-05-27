import os
import json
import sqlite3
import pandas as pd
import database_config as config
from tqdm import tqdm
from datetime import datetime, timedelta
from db_data_downloader.downloader_base import DownloaderBase
from db_data_uploader.uploader_baostock import UploaderBaoStock
from db_factor_prebuilder.prebuilder_factor import PrebuilderFactor


def init_database(database_path):
    # 检测数据库状态
    if not os.path.exists(database_path):
        # 如果数据库文件不存在，SQLite将会创建一个
        conn = sqlite3.connect(database_path)
        print(f"数据库 {database_path} 创建成功。")
        conn.close()
    else:
        print(f"数据库 {database_path} 已经存在。")


def init_database_schema(database_path, database_schema_path):
    conn = sqlite3.connect(database_path)
    print(f"数据库 {database_path} 连接成功。")
    # 创建一个cursor对象来帮助执行SQL语句
    cursor = conn.cursor()
    # 读取SQL模式文件
    with open(database_schema_path, "r") as f:
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


if __name__ == "__main__":
    try:
        # 数据库相关配置
        DATABASE_PATH = "./hh_quant_auto.db"
        DATABASE_SCHEMA_PATH = "./database_schema.sql"
        init_database(DATABASE_PATH)  # 初始化数据库
        init_database_schema(DATABASE_PATH, DATABASE_SCHEMA_PATH)  # 初始化数据表

        # 初始化数据库连接
        db_conn = sqlite3.connect(DATABASE_PATH)
        # 初始化Downloader
        db_downloader = DownloaderBase(db_conn=db_conn, db_config=config)
        # 初始化Uploader（可扩展其他uploader）
        db_uploader_baostock = UploaderBaoStock(db_conn=db_conn, db_config=config, db_downloader=db_downloader)
        db_uploader_baostock._bs_login()
        # 初始化Prebuilder
        db_prebuilder_factor = PrebuilderFactor(db_conn=db_conn, db_config=config, db_downloader=db_downloader)

        # 计算开始日期 + 结束日期
        # update_base_info = True
        # try:
        #     last_date = db_downloader._download_history_trade_date()["datetime"].max()  # 计算目前库中最新的日期
        #     start_date = datetime.strftime(datetime.strptime(last_date, "%Y-%m-%d") + timedelta(days=1), "%Y-%m-%d")  # 开始日期 = 最新日期 + 1（第二天）
        #     end_date = datetime.strftime(datetime.now(), "%Y-%m-%d")  # 结束日期 = 今日
        # except:
        #     start_date = "2000-01-01"  # 默认初始日期
        #     end_date = "2024-01-01"  # 默认结束日期

        # temp
        update_base_info = False
        start_date = "2000-01-01"
        end_date = "2024-05-14"

        # 确保开始日期 <= 结束日期
        if start_date <= end_date:
            print(f"Current Process StartDate: {start_date}, EndDate: {end_date} ...")
            if update_base_info:
                db_uploader_baostock._update_all_stock_info()
            # 1. 开始更新基础数据至本地数据库
            # db_uploader_baostock._update_start(start_date, end_date)
            # 2. 开始更新基础特征至本地数据库
            db_prebuilder_factor._update_start(start_date, end_date)
        else:
            print(f"已经是最新数据啦...start: {start_date}, end: {end_date}")

        # 关闭数据库
        db_uploader_baostock._bs_logout()
        db_conn.close()
    except Exception as e:
        print(f"Database main exception: {e}")
