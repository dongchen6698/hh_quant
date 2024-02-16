# 1. 环境配置（pyenv or conda）
* 安装pyenv版本管理工具
* 通过pyenv安装相应python版本

# 2. 搭建相关的环境
创建虚拟环境：python -m venv .venv
激活虚拟环境：source .venv/bin/activate
安装相关依赖：pip install xxxx
退出虚拟环境：deactivate

# 3. 相关工具包介绍：
> * Python
> * Vscode：变成开发工具IDE
> * AkShare｜Tushare：用来获取股票数据和推送钉钉消息
> * streamlit：用于制作web监控页面
> * Tensorflow｜Sklearn：机器学习 & 深度学习工具
> * Pandas & Numpy：数据分析处理工具
> * matplotlib：数据可视化工具
> * backtrader: 量化回测框架
> * quantstats: 衡量策略绩效指标的python lib库，用于投资组合分析
> * 指标计算工具: pandas_ta, Ta-Lib(查看安装教程)
    * ta-lib安装：
        * 首先通过：brew install ta-lib, 然后再运行：pip install ta-lib
> * pyfolio: quantopian的可视化分析工具
> * beekeeper: 本地数据库工具（免费）
    * https://github.com/beekeeper-studio/beekeeper-studio
> * Crontab: linux Crontab 定时任务

# 4. 回测流程
> * 1. cd backtest # 进入回测目录
> * 2. cd backtest_data & python download_backtest_data.py # 下载回测数据 & 基准数据
> * 3. python backtest_engine.py # 启动回测