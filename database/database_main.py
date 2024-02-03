import sqlite3


def init_database(sql_file_path="database_schema.sql"):
    # 创建连接对象
    conn = sqlite3.connect("example.db")
    # 创建游标对象
    cur = conn.cursor()
    # 打开SQL文件
    with open("sql_file_path", "r") as f:
        sql = f.read()
    # 执行SQL文件
    cur.executescript(sql)
    # 提交更改
    conn.commit()
    # 关闭连接
    conn.close()


if __name__ == "__main__":
    init_database()
