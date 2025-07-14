from binance.client import Client
from binance.exceptions import BinanceAPIException
import time
from Config import API_KEY, PRIVATE_KEY
import Account

class Trade:
    def __init__(self, symbol):
        self.api_key = API_KEY
        self.private_key = PRIVATE_KEY
        self.symbol = symbol
        self.client = Client(self.api_key, self.private_key)
        self.account = Account.Account(symbol)

    def place_order(self, side, quantity, entry_price, take_profit_price, stop_loss_price):
        leverage = 10
        try:
            self.client.futures_change_leverage(symbol=self.symbol, leverage=leverage)
        except Exception as e:
            print(f"❌ 設定槓桿失敗: {e}")
            return None

        position_side = 'LONG' if side == 'BUY' else 'SHORT'
        order_price = round(entry_price, 2)
        order_type = None

        # 嘗試限價開倉
        try:
            limit_order = self.client.futures_create_order(
                symbol=self.symbol,
                side=side,
                type='LIMIT',
                quantity=quantity,
                price=order_price,
                timeInForce='GTC',
                positionSide=position_side
            )
            print(f"⏳ 限價開倉單送出: {limit_order['orderId']}")
        except Exception as e:
            print(f"❌ 限價單下單失敗: {e}")
            return None

        # 等待成交
        filled = False
        fill_price = None
        for _ in range(10):
            time.sleep(1)
            try:
                order_status = self.client.futures_get_order(
                    symbol=self.symbol,
                    orderId=limit_order['orderId'],
                    recvWindow=5000
                )
                if order_status['status'] == 'FILLED':
                    filled = True
                    fill_price = float(order_status['avgPrice'])
                    print(f"✅ 限價單成交於 {fill_price}")
                    order_type = 0.0002
                    break
            except Exception as e:
                print(f"⚠️ 查詢限價單狀態失敗: {e}")
                continue

        # 限價單未成交則改市價
        if not filled:
            try:
                self.client.futures_cancel_order(symbol=self.symbol, orderId=limit_order['orderId'])
                print("⚠️ 限價單未成交，已取消，改用市價單")
            except Exception as e:
                print(f"❌ 撤銷限價單失敗: {e}")
                try:
                    order_status = self.client.futures_get_order(
                        symbol=self.symbol,
                        orderId=limit_order['orderId'],
                        recvWindow=5000
                    )
                    if order_status['status'] == 'FILLED':
                        filled = True
                        fill_price = float(order_status['avgPrice'])
                        print(f"✅ 限價單最終成交於 {fill_price}")
                except Exception as e2:
                    print(f"❌ 查詢限價單最終狀態失敗: {e2}")

            if not filled:
                try:
                    market_order = self.client.futures_create_order(
                        symbol=self.symbol,
                        side=side,
                        type='MARKET',
                        quantity=quantity,
                        positionSide=position_side
                    )
                    order_status = self.client.futures_get_order(
                        symbol=self.symbol,
                        orderId=market_order['orderId'],
                        recvWindow=5000
                    )
                    if order_status['status'] == 'FILLED':
                        filled = True
                        fill_price = float(order_status['avgPrice'])
                        print(f"✅ 市價單成交於 {fill_price}")
                        order_type = 0.0005
                except Exception as e:
                    print(f"❌ 市價單下單或查詢失敗: {e}")
                    return None

        if not filled or fill_price is None:
            print("❌ 無法獲得成交價格，放棄建倉")
            return None

        # 計算 TP / SL 價格
        if side == 'BUY':
            tp_price = round(fill_price + (take_profit_price - entry_price), 1)
            sl_price = round(fill_price - (entry_price - stop_loss_price), 1)
        else:
            tp_price = round(fill_price - (entry_price - take_profit_price), 1)
            sl_price = round(fill_price + (stop_loss_price - entry_price), 1)

        # 建立 TP 單
        try:
            tp_order = self.client.futures_create_order(
                symbol=self.symbol,
                side='SELL' if side == 'BUY' else 'BUY',
                type='TAKE_PROFIT',
                quantity=quantity,
                price=tp_price,
                stopPrice=tp_price,
                timeInForce='GTC',
                positionSide=position_side,
                workingType='CONTRACT_PRICE',
            )
            print(f"📈 止盈單建立成功: {tp_order['orderId']}")
        except Exception as e:
            print(f"❌ 止盈單建立失敗: {e}")

        # 建立 SL 單
        try:
            sl_order = self.client.futures_create_order(
                symbol=self.symbol,
                side='SELL' if side == 'BUY' else 'BUY',
                type='STOP_MARKET',
                stopPrice=sl_price,
                closePosition=True,
                positionSide=position_side,
                workingType='CONTRACT_PRICE',
            )
            print(f"📉 止損單建立成功: {sl_order['orderId']}")
        except Exception as e:
            print(f"❌ 止損單建立失敗: {e}")

        return {
            "entry_price": fill_price,
            "take_profit": tp_price,
            "stop_loss": sl_price,
            "quantity": quantity,
            "side": side,
            "order_type": order_type
        }
