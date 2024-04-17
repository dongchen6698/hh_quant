# 2. 搭建相关的环境
创建虚拟环境：conda create -n quant python=3.8.10
激活虚拟环境：conda activate quant
安装相关依赖：pip install xxxx OR conda install xxx
退出虚拟环境：conda deactivate

# 3. 目前使用的相关工具包介绍：
> * Python
> * Vscode：变成开发工具IDE
> * AkShare｜Tushare：用来获取股票数据和推送钉钉消息
> * Baostock:
    * pip install baostock -i https://pypi.tuna.tsinghua.edu.cn/simple/ --trusted-host pypi.tuna.tsinghua.edu.cn
> * Tensorflow｜Sklearn：机器学习 & 深度学习工具
> * Pandas & Numpy：数据分析处理工具
> * matplotlib：数据可视化工具
> * backtrader: 量化回测框架

# 4. 研究方面相关工具包介绍：
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

# Todos:
    1. 数据层面
        * 使用更高质量的数据源（TuShare、聚宽数据、等）
        * 自建或搜寻更有效的另类数据（新闻、舆情、等）
    2. 特征层面
        * 构建更有效的因子
        * 使用机器学习的方式自动化挖掘更多有效因子
        * 动量因子、趋势因子、基本面因子、等各种补充内容（可参考alpha101并完善表达式引擎内容）
    3. 模型层面
        * 特征交互、降噪、引入序列交互等
    4. 策略层面
        * 完善交易策略细节，做好风控+仓位控制等
    5. 其他：
        * 深度理解回测结果中各个参数 & 指标的含义，并有针对性的打磨策略
        * 模拟平台对接，回测数据可视化探查+CaseByCase分析
        * 实盘验证

