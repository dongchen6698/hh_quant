# 2. 搭建相关的环境
创建虚拟环境：conda create -n YOUR_ENV_NAME python=3.8.10
激活虚拟环境：conda activate YOUR_ENV_NAME
安装相关依赖：pip install xxxx OR conda install xxx
退出虚拟环境：conda deactivate

# 3. 相关工具包介绍：
> * Python
> * Vscode：变成开发工具IDE
> * AkShare｜Tushare：用来获取股票数据和推送钉钉消息
> * Baostock:
    * pip install baostock -i https://pypi.tuna.tsinghua.edu.cn/simple/ --trusted-host pypi.tuna.tsinghua.edu.cn
> * Tensorflow｜Sklearn：机器学习 & 深度学习工具
> * Pandas & Numpy：数据分析处理工具
> * matplotlib：数据可视化工具
> * backtrader: 量化回测框架
> * streamlit：用于制作web监控页面
> * quantstats: 衡量策略绩效指标的python lib库，用于投资组合分析
> * 指标计算工具: pandas_ta, Ta-Lib(查看安装教程)
    * ta-lib安装：
        * 首先通过：brew install ta-lib, 然后再运行：pip install ta-lib
> * pyfolio: quantopian的可视化分析工具
> * beekeeper: 本地数据库工具（免费）
    * https://github.com/beekeeper-studio/beekeeper-studio
> * Crontab: linux Crontab 定时任务
> * alphalens: 分析因子有效性
    * pip install alphalens-reloaded

# 4. 回测流程
> * 1. cd backtest # 进入回测目录
> * 2. cd backtest_data & python download_backtest_data.py # 下载回测数据 & 基准数据
> * 3. python backtest_engine.py # 启动回测

# 5. 远程
root@39.107.56.243