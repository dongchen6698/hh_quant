import sqlite3
import database_config as db_config
from downloader.akshare_downloader import AkShareDownloader


def init_databse():
    # 连接到SQLite数据库
    # 如果数据库文件不存在，SQLite将会创建一个
    conn = sqlite3.connect(db_config.DATABASE_PATH)
    # 创建一个cursor对象来帮助执行SQL语句
    cursor = conn.cursor()
    # 读取SQL模式文件
    with open(db_config.DATABASE_SCHEMA_PATH, "r") as f:
        schema_sql = f.read()
    # 使用executescript()执行SQL脚本
    # 如果.sql文件包含多个SQL语句，确保它们以分号结束
    cursor.executescript(schema_sql)
    # 提交事务
    conn.commit()
    # 关闭cursor和连接
    cursor.close()
    conn.close()
    print(f"数据库和表已经从文件 {db_config.DATABASE_SCHEMA_PATH} 创建于 {db_config.DATABASE_PATH}")


def download_data():
    db_conn = sqlite3.connect(db_config.DATABASE_PATH)
    start_date = "20000101"
    end_date = "20050101"
    # 初始化downloader
    downloader = AkShareDownloader(db_conn=db_conn, start_date=start_date, end_date=end_date)
    downloader._download_stock_trade_date()
    downloader._download_stock_base_info()
    downloader._download_stock_individual_info()
    downloader._download_stock_history_info()
    db_conn.close()


def main():
    # 初始化数据库
    init_databse()
    # 插入数据
    download_data()


if __name__ == "__main__":
    main()
