from binance.client import Client
from binance.exceptions import BinanceAPIException, BinanceRequestException
from Config import API_KEY, PRIVATE_KEY

class Account:
    def __init__(self, symbol):
        self.api_key = API_KEY
        self.private_key = PRIVATE_KEY
        self.symbol = symbol

        try:
            self.client = Client(self.api_key, self.private_key)
            self.client.API_URL = "https://fapi.binance.com"
            self.client._auto_timestamp = True
        except Exception as e:
            print("❌ 初始化 Binance 客戶端時失敗")
            print(e)
            self.client = None

    def get_balance(self):
        if not self.client:
            return None
        try:
            balance = self.client.futures_account_balance(recvWindow=5000)
            usdt_balance = next((item for item in balance if item['asset'] == 'USDT'), None)

            if usdt_balance:
                print(f"✅ 成功取得資金餘額：{usdt_balance['balance']} USDT")
                return float(usdt_balance['balance'])
            else:
                print("⚠️ 未找到 USDT 餘額")
                return None

        except (BinanceAPIException, BinanceRequestException, Exception) as e:
            print("❌ 取得資金餘額時發生錯誤：")
            print(e)
            return None

    def get_position(self):
        if not self.client:
            return None
        try:
            positions = self.client.futures_position_information(symbol=self.symbol, recvWindow=5000)
            if positions:
                position = positions[0]
                amt = float(position.get('positionAmt', 0))
                if amt != 0:
                    print(f"✅ 持倉資訊：方向 {'多' if amt > 0 else '空'}，倉位大小 {amt}")
                else:
                    print("⚠️ 持倉為 0")
                return position
            else:
                print("⚠️ 查無持倉")
                return None
        except (BinanceAPIException, BinanceRequestException, Exception) as e:
            print("❌ 取得持倉資訊時錯誤：")
            print(e)
            return None

    def get_open_orders(self):
        if not self.client:
            return None
        try:
            orders = self.client.futures_get_open_orders(symbol=self.symbol, recvWindow=5000)
            print(f"✅ 共取得 {len(orders)} 筆未成交訂單")
            return orders
        except (BinanceAPIException, BinanceRequestException, Exception) as e:
            print("❌ 取得未成交訂單時錯誤：")
            print(e)
            return None

    def get_account_info(self):
        if not self.client:
            return None
        try:
            info = self.client.futures_account(recvWindow=5000)
            return info
        except (BinanceAPIException, BinanceRequestException, Exception) as e:
            print("❌ 取得帳戶資訊失敗：")
            print(e)
            return None

    def get_leverage(self):
        if not self.client:
            return None
        try:
            pos_info = self.client.futures_position_information(symbol=self.symbol, recvWindow=5000)
            if pos_info and len(pos_info) > 0:
                leverage = float(pos_info[0]['leverage'])
                print(f"✅ 當前槓桿為: {leverage} 倍")
                return leverage
            else:
                return None
        except (BinanceAPIException, BinanceRequestException, Exception) as e:
            print("❌ 查詢槓桿失敗：")
            print(e)
            return None
