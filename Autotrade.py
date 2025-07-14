import pytz
import Account
import Trade 
import Klines
import ThreeBarReversalStrategy
import datetime
import time
import math
import json, os

class Autotrade:
    def __init__(self):
        self.symbol = "BTCUSDT"
        self.account = Account.Account(self.symbol)
        self.trade = Trade.Trade(self.symbol)
        self.klines = Klines.Klines(self.symbol, '30m', 30)
        self.strategy = ThreeBarReversalStrategy.ThreeBarReversalStrategy()

    def order(self, side, quantity, entry_price, take_profit_price, stop_loss_price):
        try:
            return self.trade.place_order(
                side=side, 
                quantity=quantity, 
                entry_price=entry_price,
                take_profit_price=take_profit_price,
                stop_loss_price=stop_loss_price)
        except Exception as e:
            print(f"❌ 下單失敗: {e}")
            return None

    def price_monitor(self):
        try:
            return self.klines.nowFuturesPrice()
        except Exception as e:
            print(f"❌ 取得現價失敗: {e}")
            return None

    def get_position(self):
        try:
            return self.account.get_position()
        except Exception as e:
            print(f"❌ 取得倉位資訊失敗: {e}")
            return None

    def save_trade_state(self, entry_price, take_profit, stop_loss, side, quantity, risk_ratio):
        state = {
            "has_position": True,
            "entry_price": entry_price,
            "take_profit": take_profit,
            "stop_loss": stop_loss,
            "side": side,
            "quantity": quantity,
            "risk_ratio": risk_ratio
        }
        try:
            with open("trade_state.json", "w") as f:
                json.dump(state, f)
        except Exception as e:
            print(f"❌ 儲存交易狀態失敗: {e}")

    # 結單報告（單次交易的盈虧）
    def report(self, entry_price, exit_price, side, quantity, order_type_fee=None):
        cost = quantity * entry_price
        sell = quantity * exit_price
        s_fee = 0.0002
        b_fee = order_type_fee if order_type_fee else 0.0002

        gross_result = sell - cost if side == "BUY" else cost - sell
        net_result = gross_result - (cost * b_fee) - (sell * s_fee)
        percent = (net_result / cost) * 100 if cost != 0 else 0

        print("📊 出場報告：")
        print(f"    入場價格: {entry_price}")
        print(f"    出場價格: {exit_price}")
        print(f"    倉位方向: {side}")
        print(f"    倉位大小: {quantity}")
        print(f"    成本金額: {round(cost, 4)}")
        print(f"    淨損益: {round(net_result, 4)} USDT")
        print(f"    報酬率: {round(percent, 2)}%")

        return round(net_result, 4), round(percent, 2)
    
    def run(self):
        try:
            balance = self.account.get_balance()
        except Exception as e:
            print(f"❌ 取得資金失敗: {e}")
            print("跳過本次執行")
            return None

        now = datetime.datetime.now(pytz.timezone("Asia/Taipei"))
        aligned = now.replace(minute=(now.minute // 30) * 30, second=0, microsecond=0)
        print("現在時間:", now)
        print("目前剩餘資金:", balance)

        # req
        try:
            df = self.klines.getFuturesKlines()
        except Exception as e:
            print("❌ 無法取得 K 棒資料：", e)
            print("跳過本次執行")
            return None

        print("正在確認K棒時間")
        while True:
            try:
                if df.iloc[-1]["Timestamp"] == aligned:
                    break
                print("正在等待K棒形成")
                time.sleep(1)
                df = self.klines.getFuturesKlines()
            except Exception as e:
                print("❌ 取得 K 棒時間時出錯：", e)
                print("跳過本次執行")
                return None

        latest_bar_time = df.iloc[-1]["Timestamp"]
        print(f"K棒時間確認完畢，最新K棒時間:{latest_bar_time}")

        print("正在取得策略執行結果")
        try:
            signal = self.strategy.check_entry_signal(df)
        except Exception as e:
            print("❌ 執行策略判斷時出錯：", e)
            print("跳過本次執行")
            return None

        print("執行結果取得完成")

        if signal is not None:
            try:
                direction, entry_price, take_profit, stop_loss, risk_ratio = signal
                print("現在時間:", datetime.datetime.now())
                print("準備進場")
                try:
                    self.account.client.futures_cancel_all_open_orders(symbol=self.symbol)
                except Exception as e:
                    print("❌ 撤銷舊訂單失敗：", e)
                    print("跳過本次執行")
                    return None

                print("目前剩餘資金:", balance)
                print("方向:", direction)
                print("入場價格:", entry_price)
                print("獲利價格:", take_profit)
                print("止損價格:", stop_loss)

                raw_qty = (0.5 * balance * 10) / entry_price
                quantity = round(raw_qty, 3)

                order_result = self.order(
                    side=direction,
                    quantity=quantity,
                    entry_price=entry_price,
                    take_profit_price=take_profit,
                    stop_loss_price=stop_loss
                )

                if order_result is not None:
                    entry_price = order_result["entry_price"]
                    take_profit = order_result["take_profit"]
                    stop_loss = order_result["stop_loss"]
                    self.save_trade_state(entry_price, take_profit, stop_loss, direction, quantity, risk_ratio)
                    if direction == "BUY":
                        while True:
                            if self.price_monitor() >= take_profit:
                                print(datetime.datetime.now())
                                print("現價:",self.price_monitor())
                                print("倉位方向:",direction)
                                print("獲利出場，請確認APP資訊")
                                cost =  quantity * entry_price
                                price_move_rate = take_profit/entry_price
                                b_fee = order_result["order_type"]
                                s_fee = 0.0002
                                sell = take_profit * quantity
                                result = cost * price_move_rate - cost - (cost*b_fee) - (sell * s_fee)
                                print(f"預估淨獲利:{result}")
                                print(f"預估餘額:{balance+result}")
                                break
                            elif self.price_monitor() <= stop_loss: 
                                print(datetime.datetime.now())
                                print("現價:",self.price_monitor())
                                print("倉位方向:",direction)
                                print("止損出場，請確認APP資訊")
                                cost =  quantity * entry_price
                                price_move_rate = stop_loss/entry_price
                                b_fee = order_result["order_type"]
                                s_fee = 0.0002
                                sell = take_profit * quantity
                                result = cost * price_move_rate - cost - (cost*b_fee) - (sell * s_fee)
                                print(f"預估淨損失:{result}")
                                print(f"預估餘額:{balance+result}")
                                break
                            else:
                                print(
                                    "            ♡ ♡ ∧___∧ ♡ ♡ \n" 
                                    "          + ♡ ( ⌯・-・⌯) ♡ +\n"
                                    "        ┏━━━━━━♡━ U U━♡━━━━━━┓\n" 
                                   f"        ♡{datetime.datetime.now()}♡\n"
                                   f"        ♡    倉位方向:{direction}    ♡\n"
                                   f"        ♡     損益比:1:{risk_ratio}     ♡\n"
                                   f"        ♡  入場價格:{order_result['entry_price']} ♡\n"
                                   f"        ♡    現價:{self.price_monitor()}   ♡\n"
                                   f"        ♡ 價格離入場價:{round(self.price_monitor() - entry_price,1)} ♡\n"
                                   f"        ♡  獲利價格:{round(take_profit,1)} ♡\n"
                                   f"        ♡  止損價格:{round(stop_loss,1)} ♡\n"
                                    "        ┗━♡━━━━━━━━━━━━━━━━♡━┛\n"
                                )
                                time.sleep(30)
                    if direction == "SELL":
                        while True:
                            if self.price_monitor() <= take_profit:
                                print(datetime.datetime.now())
                                print("現價:",self.price_monitor())
                                print("倉位方向:",direction)
                                print("獲利出場，請確認APP資訊")
                                cost =  quantity * entry_price
                                price_move_rate = stop_loss/entry_price
                                b_fee = order_result["order_type"]
                                s_fee = 0.0002
                                sell = take_profit * quantity
                                result = abs(cost * price_move_rate - cost) - (cost*b_fee) - (sell * s_fee)
                                print(f"預估淨獲利:{result}")
                                print(f"預估餘額:{balance+result}")
                                break
                            elif self.price_monitor() >= stop_loss: 
                                print(datetime.datetime.now())
                                print("現價:",self.price_monitor())
                                print("倉位方向:",direction)
                                print("止損出場，請確認APP資訊")
                                cost =  quantity * entry_price
                                price_move_rate = take_profit/entry_price
                                b_fee = order_result["order_type"]
                                s_fee = 0.0002
                                sell = take_profit * quantity
                                result = 0 - (cost * price_move_rate - cost) - (cost*b_fee) - (sell * s_fee)
                                print(f"預估淨損失:{result}")
                                print(f"預估餘額:{balance+result}")
                                break
                            else:
                                print(
                                    "            ♡ ♡ ∧___∧ ♡ ♡ \n" 
                                    "          + ♡ ( ⌯・-・⌯) ♡ +\n"
                                    "        ┏━━━━━━♡━ U U━♡━━━━━━┓\n" 
                                   f"        ♡{datetime.datetime.now()}♡\n"
                                   f"        ♡    倉位方向:{direction}    ♡\n"
                                   f"        ♡     損益比:1:{risk_ratio}     ♡\n"
                                   f"        ♡  入場價格:{order_result['entry_price']} ♡\n"
                                   f"        ♡    現價:{self.price_monitor()}   ♡\n"
                                   f"        ♡ 價格離入場價:{round(self.price_monitor() - entry_price,1)} ♡\n"
                                   f"        ♡  獲利價格:{round(take_profit,1)} ♡\n"
                                   f"        ♡  止損價格:{round(stop_loss,1)} ♡\n"
                                    "        ┗━♡━━━━━━━━━━━━━━━━♡━┛\n"
                                )
                                time.sleep(30)
                else: 
                    print("下單失敗")
                    return None
            except Exception as e:
                print("❌ 處理進場流程時發生錯誤：", e)
                print("跳過本次執行")
                return None
        else:
            print("現價:",self.klines.nowFuturesPrice())
            print("暫無進場機會\n")
            return None

    def monitor_existing_position(self):
        if not os.path.exists("trade_state.json"):
            print("📭 無上次交易紀錄，略過監控")
            return

        with open("trade_state.json", "r") as f:
            state = json.load(f)

        if not state.get("has_position", False):
            print("📭 上次紀錄無持倉，略過監控")
            return

        position = self.account.get_position()
        if position == None:
            print("📭 帳戶實際無倉位，清除紀錄")
            os.remove("trade_state.json")
            return

        entry_price = state["entry_price"]
        take_profit = state["take_profit"]
        stop_loss = state["stop_loss"]
        side = state["side"]
        risk_ratio = state["risk_ratio"] 

        print("📌 偵測到持倉，啟動監控：")

        while True:
            current_price = self.price_monitor()
            if current_price is None:
                time.sleep(5)
                continue

            if side == "BUY":
                if self.price_monitor() >= take_profit:
                    print(datetime.datetime.now())
                    print("現價:",self.price_monitor())
                    print("倉位方向:",side)
                    print("獲利出場，請確認APP資訊")
                    break
                elif self.price_monitor() <= stop_loss: 
                    print(datetime.datetime.now())
                    print("現價:",self.price_monitor())
                    print("倉位方向:",side)
                    print("止損出場，請確認APP資訊")
                    break
                else:
                    print(
                            "            ♡ ♡ ∧___∧ ♡ ♡ \n" 
                            "          + ♡ ( ⌯・-・⌯) ♡ +\n"
                            "        ┏━━━━━━♡━ U U━♡━━━━━━┓\n" 
                           f"        ♡{datetime.datetime.now()}♡\n"
                           f"        ♡    倉位方向:{side}    ♡\n"
                           f"        ♡     損益比:1:{risk_ratio}     ♡\n"
                           f"        ♡  入場價格:{entry_price} ♡\n"
                           f"        ♡    現價:{self.price_monitor()}   ♡\n"
                           f"        ♡ 價格離入場價:{round(self.price_monitor() - entry_price,1)} ♡\n"
                           f"        ♡  獲利價格:{round(take_profit,1)} ♡\n"
                           f"        ♡  止損價格:{round(stop_loss,1)} ♡\n"
                            "        ┗━♡━━━━━━━━━━━━━━━━♡━┛\n"
                    )
            else:  # SELL 倉位
                if self.price_monitor() <= take_profit:
                    print(datetime.datetime.now())
                    print("現價:",self.price_monitor())
                    print("倉位方向:",side)
                    print("獲利出場，請確認APP資訊")
                    break
                elif self.price_monitor() >= stop_loss: 
                    print(datetime.datetime.now())
                    print("現價:",self.price_monitor())
                    print("倉位方向:",side)
                    print("止損出場，請確認APP資訊")
                    break
                else:
                    print(
                            "            ♡ ♡ ∧___∧ ♡ ♡ \n" 
                            "          + ♡ ( ⌯・-・⌯) ♡ +\n"
                            "        ┏━━━━━━♡━ U U━♡━━━━━━┓\n" 
                           f"        ♡{datetime.datetime.now()}♡\n"
                           f"        ♡    倉位方向:{side}    ♡\n"
                           f"        ♡     損益比:1:{risk_ratio}     ♡\n"
                           f"        ♡  入場價格:{entry_price} ♡\n"
                           f"        ♡    現價:{self.price_monitor()}   ♡\n"
                           f"        ♡ 價格離入場價:{round(self.price_monitor() - entry_price,1)} ♡\n"
                           f"        ♡  獲利價格:{round(take_profit,1)} ♡\n"
                           f"        ♡  止損價格:{round(stop_loss,1)} ♡\n"
                            "        ┗━♡━━━━━━━━━━━━━━━━♡━┛\n"
                    )
            time.sleep(30)

        os.remove("trade_state.json")

    def test(self):
        balance = self.get_balance()
        step_size = 0.001 #BTC最小投入額
        raw_qty = (balance) / self.klines.nowFuturesPrice() #想投入的金額/現價
        precision = abs(int(round(math.log10(step_size))))
        adjusted_qty = math.floor(raw_qty / step_size) * step_size
        print(
            self.order(
            side = "BUY", 
            quantity=0.002, 
            entry_price = self.klines.nowFuturesPrice(),
            take_profit_price = 107428,
            stop_loss_price = 103700)
        )