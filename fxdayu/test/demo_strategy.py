from datetime import datetime
import pandas as pd


avg_pct = 0.3
diff = 0.0


def initialize(context, data):
    # context.time_schedule(
    #     week_end,
    #     context.time_rules(isoweekday=5)
    # )
    # context.router.set_commission(per_value=0.0005, min_cost=5)
    context.pct_dict = dict([('000001', avg_pct), ('600016', avg_pct+diff), ('600036', avg_pct-diff)])


def handle_data(context, data):
    portfolio = context.portfolio

    for symbol in context.tickers:
        order_target_percent(symbol, context.pct_dict[symbol])
    pass


def week_end(context, data):
    portfolio = context.portfolio

    for symbol in context.tickers:
        order_target_percent(symbol, context.pct_dict[symbol])


if __name__ == '__main__':
    from test_backtest import NewBackTrader
    trader = NewBackTrader()
    trader['data'].kwargs.update({'port': 27018, 'host': '192.168.0.103'})
    trader['router'].kwargs.update({'deal_model': 0})
    trader.initialize()
    trader.back_test(
        'demo_strategy.py',
        ['000001', '600016', '600036'], 'D', datetime(2016, 1, 1),
        ticker_type='HS', params={'diff': 0.05, 'avg_pct': 0.3}, save=True
    )

    # ot = trader.output('strategy_summary', 'risk_indicator')
    # print ot
    #
    # optimizer = Optimizer()
    # optimizer['data'].kwargs.update({'port': 10001})
    # optimizer['router'].kwargs.update({'deal_model': BACKTESTDEALMODE.THIS_BAR_CLOSE})
    #
    # optimizer.optimization(
    #     __import__('demo_strategy'), ['000001', '600016', '600036'],
    #     'D', datetime(2016, 1, 1), ticker_type='HS', save=True,
    #     avg_pct=[0.2, 0.25, 0.3], diff=[0.05, 0.1]
    # )
