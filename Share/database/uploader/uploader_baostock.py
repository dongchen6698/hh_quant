import baostock as bs
import pandas as pd
from datetime import datetime
from tqdm import tqdm
import time
from .uploader_base import UploaderBase


class AkShareUploader(UploaderBase):
    def __init__(self, db_conn, start_date="20000101", end_date="20500101") -> None:
        self.db_conn = db_conn
        self.start_date = self._transfer_datetime(start_date)
        self.end_date = self._transfer_datetime(end_date)

    def _transfer_datetime(self, datetime_str):
        return datetime.strptime(datetime_str, "%Y%m%d").strftime("%Y-%m-%d")

    def _bs_login():
        #### 登陆系统 ####
        lg = bs.login()
        # 显示登陆返回信息
        print("login respond error_code:" + lg.error_code)
        print("login respond  error_msg:" + lg.error_msg)

    def _bs_logout():
        #### 登出系统 ####
        bs.logout()
