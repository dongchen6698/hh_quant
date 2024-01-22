import sys
from config import global_config, backtest_config
from strategies.simple_strategies.moving_average_strategy import MovingAverageStrategy
from backtest.backtest_engine import BacktestEngine

# from live.trade_executor import TradeExecutor
# from simulation.simulation_engine import SimulationEngine


def main():
    # 如果是回测模式
    if global_config.MODE == "backtest":
        backtest_engine = BacktestEngine(MovingAverageStrategy, backtest_config)
        backtest_engine.run_backtest()
        backtest_engine.evaluate_performance()

    # # 如果是模拟交易模式
    # elif global_config.MODE == "simulation":
    #     simulation_engine = SimulationEngine(data, strategy)
    #     simulation_engine.run_simulation()

    # # 如果是实盘交易模式
    # elif global_config.MODE == "live":
    #     trade_executor = TradeExecutor(strategy)
    #     trade_executor.start_trading()

    # 其他模式
    else:
        print("Invalid mode. Please choose 'backtest', 'simulation', or 'live'.")
        sys.exit(1)


if __name__ == "__main__":
    main()
