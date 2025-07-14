import pytz
import Backtest
import datetime
import Autotrade
#回測
# print(r.account.client.futures_get_order(symbol=r.symbol, orderId="691230320005"))
# print("回測開始")

# now = datetime.datetime.now(pytz.timezone("Asia/Taipei"))
# aligned = now.replace(minute=(now.minute // 30) * 30, second=0, microsecond=0)
# hour =now.hour
# minute = now.minute
# second = now.second
# date = datetime.date.today().strftime('%Y/%m/%d')
# print(
#     "            ♡ ♡ ∧___∧ ♡ ♡ \n" 
#     "          + ♡ ( ⌯・-・⌯) ♡ +\n"
#     "        ┏━━━━━━♡━ U U━♡━━━━━━┓\n" 
#    f"        ♡       BEARISH      ♡\n"
#    f"        ♡         BUT        ♡\n"
#    f"        ♡ VOLUME NOT ENOUGH！♡\n"
#     "        ┗━♡━━━━━━━━━━━━━━━━♡━┛\n"
# )
# simulator = Backtest.BacktestSimulator()
# simulator.ThreeBarReversalSimulate()

# r = Autotrade.Autotrade()
# if r.account.get_position() == None:
#     print(True)
# print(r.account.get_balance())

# print(r.account.client.futures_get_order(symbol=r.symbol, orderId="691230320005"))
# df = r.klines.getFuturesKlines()
# if df.iloc[-1]["Timestamp"] == aligned:
#     print("true")
# else:
#     print("false")

from binance.client import Client
c = Client("xxx", "yyy")
print(dir(c))


