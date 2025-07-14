import Autotrade
import Backtest
import time
import datetime
import random
#自動交易

# try:
# except(BinanceAPIException, BinanceRequestException) as e:
r = Autotrade.Autotrade()
print("目前版本為：2025/05/27-04:40\n"
      "成交量有達標 - 損益比1:5\n"
      "成交量未達標 - 損益比1:2\n"
      "下單同時給限價止盈止損\n"
      "平單後自動撤消另一單\n"
      "自動倉位監測\n"
      "自動校準時間\n"
      "確認新K棒形成\n"
      )

print("✅ 自動交易系統啟動")

r.monitor_existing_position()

last_minute_triggered = 99
while True:
    now = datetime.datetime.now()
    hour =now.hour
    minute = now.minute
    second = now.second
    date = datetime.date.today().strftime('%Y/%m/%d')
    # 如果現在是整點（00分）或半點（30分），且秒數在前3秒以內（防抖動）

    #測試改 時間if else 、k棒、損益比、資金、成交量判定
    if minute % 30 == 0 and second < 5 and minute != last_minute_triggered:
    # if second < 5 and minute != last_minute_triggered:
        last_minute_triggered = minute
        print(
                "       ♡ ♡ ∧___∧ ♡ ♡ \n" 
                "     + ♡ ( ⌯・v・⌯) ♡ +\n"
                "        ┏━♡━ U U━♡━┓\n"
               f"        ♡ {date}♡\n"
               f"        ♡  {'0'+str(hour) if hour <10 else hour}:{'0'+str(minute) if minute <10 else minute}:{'0'+str(second) if second <10 else second} ♡\n"  
               f"        ♡ 執行策略! ♡\n"
                "        ┗━♡━━━━━━♡━┛\n"
            )
        r.run()
    elif (minute%30 == 29):
        if random.randint(1,50) == 10 : 
            print(
                "       ♡ ♡ ∧___∧ ♡ ♡ \n" 
                "     + ♡ ( ⌯・-・⌯) ♡ +\n"
                "        ┏━♡━ U U━♡━┓\n" 
               f"        ♡ {date}♡\n"
               f"        ♡  {'0'+str(hour) if hour <10 else hour}:{'0'+str(minute) if minute <10 else minute}:{'0'+str(second) if second <10 else second} ♡\n" 
               f"        ♡ {r.price_monitor()} ♡\n"
                "        ┗━♡━━━━━━♡━┛\n"
            )
        time.sleep(1)
    else:
        # 每30秒檢查一次
        if random.randint(1,20) == 10 : 
            print(
                "       ♡ ♡ ∧___∧ ♡ ♡ \n" 
                "     + ♡ ( ⌯・-・⌯) ♡ +\n"
                "        ┏━♡━ U U━♡━┓\n" 
               f"        ♡ {date}♡\n"
               f"        ♡  {'0'+str(hour) if hour <10 else hour}:{'0'+str(minute) if minute <10 else minute}:{'0'+str(second) if second <10 else second} ♡\n" 
               f"        ♡  {r.price_monitor()} ♡\n"
                "        ┗━♡━━━━━━♡━┛\n"
            )
        time.sleep(30)  
        # time.sleep(1)
