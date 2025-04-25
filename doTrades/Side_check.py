import Operate as op
import time
import csv
from datetime import datetime
import requests  # 確保引入 requests 模組以捕獲相關異常
import pandas as pd
import pandas_ta as ta  # 替代 TA-Lib
from Config import API_KEY, FUTURES_URL  # 從 config 導入 API_KEY 和 FUTURES_URL

# 初始化變數
CHECK_INTERVAL = 5  # 每幾秒檢查一次
trade_amount = 1500  # 交易金額
trend_records = []  # 儲存趨勢記錄
current_position = None  # 當前持倉狀態 ('BUY' 或 'SELL')
reverse_count = 0  # 趨勢反轉次數
consecutive_up = 0
consecutive_down = 0
CONSECUTIVE_TRADE_THRESHOLD = 5  # 進場的連續次數閾值
CONSECUTIVE_REVERSE_THRESHOLD = 3  # 平倉的連續反轉次數閾值

# 初始化技術指標相關變數
rsi_period = 14  # RSI 的計算週期
stop_loss_percentage = 0.02  # 止損百分比
take_profit_percentage = 0.05  # 止盈百分比
max_risk_percentage = 0.02  # 單筆交易最大風險百分比

# 初始化
print(f"開始每 {CHECK_INTERVAL} 秒檢查 BTCUSDT 是升還是跌")
operate = op.Operate(symbol='BTCUSDT',timeframe='30m', limit=100)

previous_price = None

# 計算交易金額基於風險管理
def calculate_trade_amount(account_balance, entry_price):
    max_risk_amount = account_balance * max_risk_percentage
    return max_risk_amount / entry_price

try:
    # 獲取賬戶餘額
    account_balance = operate.get_account_balance()  # 獲取賬戶餘額
    print(f"賬戶餘額: {account_balance:.2f} USDT")  # 列出賬戶餘額
    # 檢查是否有未平倉交易
    current_position = operate.get_open_position('BTCUSDT')  # 假設此方法返回 {'side': 'BUY'/'SELL', 'entryPrice': float} 或 None
    if current_position:
        entry_price = current_position['entryPrice']
        side = current_position['side']
        print(f"檢測到未平倉交易，方向: {side}，進場價: {entry_price}")
        # 計算持倉總金額和盈虧
        current_price = operate.get_current_price('BTCUSDT')
        position_amount = trade_amount  # 假設持倉金額等於交易金額
        pnl = (current_price - entry_price) * (1 if side == 'BUY' else -1)
        print(f"持倉總金額: {position_amount} USDT, 盈虧: {pnl:.2f} USDT")
    else:
        print("目前無未平倉交易")
except requests.exceptions.ReadTimeout as e:
    print(f"檢查未平倉交易時出現異常: {e}")
    print("程式即將停止...")
    exit(1)  # 安全退出程式
except Exception as e:
    print(f"發生未預期的錯誤: {e}")
    print("程式即將停止...")
    exit(1)  # 安全退出程式

# 初始化 HTML 文件名稱
new_html_filename = None

while True:
    try:
        current_price = operate.get_current_price('BTCUSDT')
        if current_price is not None:
            # 獲取歷史價格數據
            historical_prices = operate.get_historical_prices('BTCUSDT', limit=100)  # 假設此方法返回最近 100 根 K 線的收盤價
            if len(historical_prices) < rsi_period:
                print("歷史數據不足，無法計算 RSI")
                time.sleep(CHECK_INTERVAL)
                continue

            # 計算 RSI
            df = pd.DataFrame(historical_prices, columns=["close"])
            df["rsi"] = ta.rsi(df["close"], length=rsi_period)
            rsi = df["rsi"].iloc[-1]
            print(f"當前 RSI: {rsi:.2f}")

            # 檢查交易量
            current_volume = historical_prices['volume']  # 假設此方法返回當前交易量
            if current_volume < 100:  # 假設 100 是最低交易量閾值
                print("交易量過低，跳過本次檢查")
                time.sleep(CHECK_INTERVAL)
                continue

            if previous_price is not None:
                price_change = current_price - previous_price
                percentage_change = (price_change / previous_price) * 100
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                if current_price > previous_price:
                    if current_position and current_position['side'] == 'SELL':
                        reverse_count += 1  # 賣空時遇到上漲，反轉次數 +1
                    else:
                        reverse_count = 0  # 方向一致時重置反轉次數
                    consecutive_up += 1
                    consecutive_down = 0
                    record = {
                        "type": "上漲",
                        "price": current_price,
                        "change": price_change,
                        "percentage": percentage_change,
                        "timestamp": timestamp,
                        "position": current_position['side'] if current_position else None,
                        "entryPrice": current_position['entryPrice'] if current_position else None,
                        "pnl": (current_price - current_position['entryPrice']) * (1 if current_position['side'] == 'BUY' else -1) if current_position else None
                    }
                    trend_records.append(record)
                    if not new_html_filename and current_position:
                        # 初始化個別檔案名稱
                        new_html_filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{current_position['side']}_{current_position['entryPrice']:.3f}.html"
                        with open(new_html_filename, mode='w', encoding='utf-8') as new_file:
                            new_file.write("<html><head><title>交易記錄</title></head><body>")
                            new_file.write("<h1>交易記錄</h1>")
                            new_file.write("<table border='1' style='border-collapse: collapse; text-align: center;'><tr><th>時間</th><th>類型</th><th>價格</th><th>變化</th><th>百分比</th><th>持倉方向</th><th>進場價格</th><th>盈虧</th><th>盈虧百分比</th></tr>")

                    if new_html_filename:  # 確保檔案名稱已初始化
                        if current_position:  # 確保 current_position 不為 None
                            pnl = (current_price - current_position['entryPrice']) * (-1 if current_position['side'] == 'SELL' else 1)
                            pnl_percentage = (pnl / current_position['entryPrice']) * 100
                        else:
                            pnl = 0
                            pnl_percentage = 0

                        with open(new_html_filename, mode='a', encoding='utf-8') as new_file:
                            new_file.write(f"<tr><td>{record['timestamp']}</td>"
                                           f"<td>{record['type']}</td>"
                                           f"<td>{'{:.3f}'.format(record['price']) if isinstance(record['price'], (int, float)) else '0.000'}</td>"
                                           f"<td>{'{:.3f}'.format(record['change']) if isinstance(record['change'], (int, float)) else '0.000'}</td>"
                                           f"<td>{'{:.3f}'.format(record['percentage']) if isinstance(record['percentage'], (int, float)) else '0.000'}%</td>"
                                           f"<td>{record['position'] if record['position'] is not None else 'N/A'}</td>"
                                           f"<td>{'{:.3f}'.format(record['entryPrice']) if isinstance(record['entryPrice'], (int, float)) else '0.000'}</td>"
                                           f"<td>{'{:.3f}'.format(pnl)}</td>"
                                           f"<td>{'{:.3f}'.format(pnl_percentage)}%</td></tr>")
                            new_file.flush()  # 確保數據立即寫入文件
                    actual_trade_amount = trade_amount if current_position else 0
                    pnl = ((current_price - current_position['entryPrice']) * actual_trade_amount / current_position['entryPrice']) * (-1 if current_position['side'] == 'SELL' else 1) if current_position else 0
                    pnl_percentage = (pnl / actual_trade_amount) * 100 if actual_trade_amount > 0 else 0
                    print(f"BTCUSDT 上漲，現價: {current_price}, 升幅: {price_change} ({percentage_change:.2f}%) 下單價格: {current_position['entryPrice'] if current_position else 'N/A'}, 金額: {actual_trade_amount}, 目前盈虧: {pnl:.2f} USDT ({pnl_percentage:.2f}%), 趨勢反轉次數: {reverse_count}, 儲存趨勢記錄數: {len(trend_records)}")
                elif current_price < previous_price:
                    if current_position and current_position['side'] == 'BUY':
                        reverse_count += 1  # 買進時遇到下跌，反轉次數 +1
                    else:
                        reverse_count = 0  # 方向一致時重置反轉次數
                    consecutive_down += 1
                    consecutive_up = 0
                    record = {
                        "type": "下跌",
                        "price": current_price,
                        "change": price_change,
                        "percentage": percentage_change,
                        "timestamp": timestamp,
                        "position": current_position['side'] if current_position else None,
                        "entryPrice": current_position['entryPrice'] if current_position else None,
                        "pnl": (current_price - current_position['entryPrice']) * (1 if current_position['side'] == 'SELL' else -1) if current_position else None
                    }
                    trend_records.append(record)
                    if not new_html_filename and current_position:
                        # 初始化個別檔案名稱
                        new_html_filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{current_position['side']}_{current_position['entryPrice']:.3f}.html"
                        with open(new_html_filename, mode='w', encoding='utf-8') as new_file:
                            new_file.write("<html><head><title>交易記錄</title></head><body>")
                            new_file.write("<h1>交易記錄</h1>")
                            new_file.write("<table border='1' style='border-collapse: collapse; text-align: center;'><tr><th>時間</th><th>類型</th><th>價格</th><th>變化</th><th>百分比</th><th>持倉方向</th><th>進場價格</th><th>盈虧</th><th>盈虧百分比</th></tr>")

                    if new_html_filename:  # 確保檔案名稱已初始化
                        if current_position:  # 確保 current_position 不為 None
                            pnl = (current_price - current_position['entryPrice']) * (-1 if current_position['side'] == 'SELL' else 1)
                            pnl_percentage = (pnl / current_position['entryPrice']) * 100
                        else:
                            pnl = 0
                            pnl_percentage = 0

                        with open(new_html_filename, mode='a', encoding='utf-8') as new_file:
                            new_file.write(f"<tr><td>{record['timestamp']}</td>"
                                           f"<td>{record['type']}</td>"
                                           f"<td>{'{:.3f}'.format(record['price']) if isinstance(record['price'], (int, float)) else '0.000'}</td>"
                                           f"<td>{'{:.3f}'.format(record['change']) if isinstance(record['change'], (int, float)) else '0.000'}</td>"
                                           f"<td>{'{:.3f}'.format(record['percentage']) if isinstance(record['percentage'], (int, float)) else '0.000'}%</td>"
                                           f"<td>{record['position'] if record['position'] is not None else 'N/A'}</td>"
                                           f"<td>{'{:.3f}'.format(record['entryPrice']) if isinstance(record['entryPrice'], (int, float)) else '0.000'}</td>"
                                           f"<td>{'{:.3f}'.format(pnl)}</td>"
                                           f"<td>{'{:.3f}'.format(pnl_percentage)}%</td></tr>")
                            new_file.flush()  # 確保數據立即寫入文件
                    actual_trade_amount = trade_amount if current_position else 0
                    pnl = ((current_price - current_position['entryPrice']) * actual_trade_amount / current_position['entryPrice']) * (-1 if current_position['side'] == 'SELL' else 1) if current_position else 0
                    pnl_percentage = (pnl / actual_trade_amount) * 100 if actual_trade_amount > 0 else 0
                    print(f"BTCUSDT 下跌，現價: {current_price}, 跌幅: {abs(price_change)} ({abs(percentage_change):.2f}%) 下單價格: {current_position['entryPrice'] if current_position else 'N/A'}, 金額: {actual_trade_amount}, 目前盈虧: {pnl:.2f} USDT ({pnl_percentage:.2f}%), 趨勢反轉次數: {reverse_count}, 儲存趨勢記錄數: {len(trend_records)}")
                else:
                    # 價格不變時，保持當前狀態，不記錄
                    print(f"BTCUSDT 價格不變，現價: {current_price}")

                if current_position:
                    # 動態計算止損和止盈價格
                    entry_price = current_position['entryPrice']
                    stop_loss_price = entry_price * (1 - stop_loss_percentage if current_position['side'] == 'BUY' else 1 + stop_loss_percentage)
                    take_profit_price = entry_price * (1 + take_profit_percentage if current_position['side'] == 'BUY' else 1 - take_profit_percentage)

                    # 檢查是否觸發止損或止盈
                    if (current_position['side'] == 'BUY' and (current_price <= stop_loss_price or current_price >= take_profit_price)) or \
                       (current_position['side'] == 'SELL' and (current_price >= stop_loss_price or current_price <= take_profit_price)):
                        print(f"觸發止損或止盈，平倉 {current_position['side']} 交易")
                        operate.close_position('BTCUSDT', current_position['side'])
                        with open(new_html_filename, mode='a', encoding='utf-8') as new_file:
                            new_file.write("</table><h2>交易已平倉 (止損/止盈)</h2>")
                        trend_records = []  # 清空記錄
                        current_position = None  # 重置持倉狀態
                        reverse_count = 0  # 重置反轉次數
                        continue

                # 若已進行交易，檢查是否需要平倉
                if current_position:
                    # 動態計算實際下單金額
                    entry_price = current_position['entryPrice']
                    side = current_position['side']
                    position_amount = trade_amount / entry_price  # 持倉數量
                    pnl = (current_price - entry_price) * position_amount * (-1 if side == 'SELL' else 1)
                    pnl_percentage = (pnl / trade_amount) * 100 if trade_amount > 0 else 0

                    # 檢查是否達到反轉次數閾值
                    if reverse_count >= CONSECUTIVE_REVERSE_THRESHOLD:
                        print(f"連續 {CONSECUTIVE_REVERSE_THRESHOLD} 次趨勢反轉，平倉 {current_position['side']} 交易")
                        operate.close_position('BTCUSDT', current_position['side'])  # 假設此方法執行平倉
                        with open(new_html_filename, mode='a', encoding='utf-8') as new_file:
                            new_file.write("</table><h2>交易已平倉</h2>")
                        trend_records = []  # 清空記錄
                        current_position = None  # 重置持倉狀態
                        reverse_count = 0  # 重置反轉次數

                # 若未進行交易，檢查是否需要進場
                if not current_position:
                    # 檢查儲存趨勢記錄的最後一筆與上一筆是否為同一趨勢
                    if len(trend_records) >= 2:
                        last_record = trend_records[-1]
                        second_last_record = trend_records[-2]
                        if last_record["type"] != second_last_record["type"]:
                            print(f"趨勢改變，清空儲存趨勢記錄。最後一筆: {last_record['type']}, 倒數第二筆: {second_last_record['type']}")
                            trend_records.clear()

                    if consecutive_up == CONSECUTIVE_TRADE_THRESHOLD and rsi < 30:
                        print(f"連續 {CONSECUTIVE_TRADE_THRESHOLD} 次上漲且 RSI < 30，買進 {trade_amount} USDT")
                        trade_amount = calculate_trade_amount(operate.get_account_balance(), current_price)
                        operate.place_order(symbol='BTCUSDT', side='BUY', amount=trade_amount)
                        current_position = {'side': 'BUY', 'entryPrice': current_price}
                        # 新建 HTML 文件
                        new_html_filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_BUY_{current_price:.3f}.html"
                        with open(new_html_filename, mode='w', encoding='utf-8') as new_file:
                            new_file.write("<html><head><title>交易記錄</title></head><body>")
                            new_file.write("<h1>交易記錄</h1>")
                            new_file.write("<table border='1' style='border-collapse: collapse; text-align: center;'><tr><th>時間</th><th>類型</th><th>價格</th><th>變化</th><th>百分比</th><th>持倉方向</th><th>進場價格</th><th>盈虧</h><th>盈虧百分比</th></tr>")
                    elif consecutive_down == CONSECUTIVE_TRADE_THRESHOLD and rsi > 70:
                        print(f"連續 {CONSECUTIVE_TRADE_THRESHOLD} 次下跌且 RSI > 70，賣空 {trade_amount} USDT")
                        trade_amount = calculate_trade_amount(operate.get_account_balance(), current_price)
                        operate.place_order(symbol='BTCUSDT', side='SELL', amount=trade_amount)
                        current_position = {'side': 'SELL', 'entryPrice': current_price}
                        # 新建 HTML 文件
                        new_html_filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_SELL_{current_price:.3f}.html"
                        with open(new_html_filename, mode='w', encoding='utf-8') as new_file:
                            new_file.write("<html><head><title>交易記錄</title></head><body>")
                            new_file.write("<h1>交易記錄</h1>")
                            new_file.write("<table border='1' style='border-collapse: collapse; text-align: center;'><tr><th>時間</th><th>類型</th><th>價格</th><th>變化</th><th>百分比</th><th>持倉方向</th><th>進場價格</th><th>盈虧</th><th>盈虧百分比</th></tr>")

            previous_price = current_price
        else:
            print("無法取得現價")
    except requests.exceptions.ReadTimeout as e:
        print(f"檢查價格時出現異常: {e}")
        print("程式即將停止...")
        exit(1)  # 安全退出程式
    except Exception as e:
        print(f"發生未預期的錯誤: {e}")
        print("程式即將停止...")
        exit(1)  # 安全退出程式

    time.sleep(CHECK_INTERVAL)
