from binance.client import Client
from Config import API_KEY, PRIVATE_KEY, USE_TESTNET, FUTURES_URL  # 使用絕對導入 PRIVATE_KEY, USE_TESTNET, FUTURES_URL  # 使用絕對導入
import pandas as pd
import time
import math
import requests
import hmac
import hashlib
import urllib.parse

# 初始化客戶端

class Operate:

    def __init__(self, symbol, timeframe, limit):
        self.symbol = symbol
        self.timeframe = timeframe
        self.limit = limit
        self.api_key = API_KEY
        self.private_key = PRIVATE_KEY
        self.client = Client(self.api_key, self.private_key, testnet=USE_TESTNET)  # 啟用測試網或主網
        if USE_TESTNET:
            self.client.FUTURES_URL = FUTURES_URL  # 使用配置中的 FUTURES_URL
        self.client._request_params = {"recvWindow": 10000}  # 增加 recvWindow
    

    def calculate_pnl(self, trades_df):
        print("正在計算盈虧...")
        try:
            # 初始化變數
            total_buy_cost_with_fee = 0
            total_sell_revenue_with_fee = 0
            total_buy_cost_without_fee = 0
            total_sell_revenue_without_fee = 0
            total_buy_commission = 0  # 買入手續費
            total_sell_commission = 0  # 賣出手續費

            # 遍歷每筆交易
            for _, trade in trades_df.iterrows():
                price = float(trade['price'])
                qty = float(trade['qty'])
                commission = float(trade['commission'])

                if trade['side'] == 'BUY':
                    total_buy_cost_with_fee += price * qty + commission
                    total_buy_cost_without_fee += price * qty
                    total_buy_commission += commission
                elif trade['side'] == 'SELL':
                    total_sell_revenue_with_fee += price * qty - commission
                    total_sell_revenue_without_fee += price * qty
                    total_sell_commission += commission

            # 總手續費
            total_commission = total_buy_commission + total_sell_commission

            # 計算扣掉手續費前的盈虧
            pnl_before_fees = total_sell_revenue_without_fee - total_buy_cost_without_fee

            # 計算總盈虧（扣掉手續費後）
            total_pnl = total_sell_revenue_with_fee - total_buy_cost_with_fee

            # 計算百分比
            pnl_percentage_before_fees = (pnl_before_fees / total_buy_cost_without_fee) * 100 if total_buy_cost_without_fee > 0 else 0
            pnl_percentage = (total_pnl / total_buy_cost_with_fee) * 100 if total_buy_cost_with_fee > 0 else 0

            # 計算手續費百分比
            commission_on_cost = (total_buy_commission / total_buy_cost_without_fee) * 100 if total_buy_cost_without_fee > 0 else 0
            commission_on_revenue = (total_sell_commission / total_sell_revenue_without_fee) * 100 if total_sell_revenue_without_fee > 0 else 0
            commission_total_percentage = (total_commission / (total_buy_cost_without_fee + total_sell_revenue_without_fee)) * 100 if (total_buy_cost_without_fee + total_sell_revenue_without_fee) > 0 else 0

            # 打印結果
            print("盈虧計算結果:")
            print(f"總成本(未扣/已扣手續費): {total_buy_cost_without_fee:.3f} / {total_buy_cost_with_fee:.3f} USDT")
            print(f"總收益(未扣/已扣手續費): {total_sell_revenue_without_fee:.3f} / {total_sell_revenue_with_fee:.3f} USDT")
            print(f"總手續費(成本/收益/總額): {total_buy_commission:.3f} ({commission_on_cost:.3f}%) / {total_sell_commission:.3f} ({commission_on_revenue:.3f}%) / {total_commission:.3f} ({commission_total_percentage:.3f}%) USDT")
            print(f"總盈虧(未扣/已扣手續費): {pnl_before_fees:.3f} ({pnl_percentage_before_fees:.3f}%) / {total_pnl:.3f} ({pnl_percentage:.3f}%) USDT")

            return {
                "total_buy_cost_without_fee": total_buy_cost_without_fee,
                "total_buy_cost_with_fee": total_buy_cost_with_fee,
                "total_sell_revenue_without_fee": total_sell_revenue_without_fee,
                "total_sell_revenue_with_fee": total_sell_revenue_with_fee,
                "total_buy_commission": total_buy_commission,
                "total_sell_commission": total_sell_commission,
                "total_commission": total_commission,
                "commission_on_cost": commission_on_cost,
                "commission_on_revenue": commission_on_revenue,
                "commission_total_percentage": commission_total_percentage,
                "pnl_before_fees": pnl_before_fees,
                "pnl_percentage_before_fees": pnl_percentage_before_fees,
                "total_pnl": total_pnl,
                "pnl_percentage": pnl_percentage
            }
        except Exception as e:
            print(f"計算盈虧時出現異常: {e}")
            return None

    def get_current_price(self, symbol):
        """
        獲取指定交易對的現價。
        :param symbol: 交易對
        :return: 現價 (float)
        """
        try:
            ticker = self.client.futures_symbol_ticker(symbol=symbol)
            current_price = float(ticker['price'])
            # print(f"{symbol} 現價: {current_price}")
            return current_price
        except Exception as e:
            print(f"取得 {symbol} 現價時出現異常: {e}")
            return None

    def get_open_position(self, symbol):
        """
        檢查是否有未平倉的交易。
        :param symbol: 交易對
        :return: 包含 'side' 和 'entryPrice' 的字典，或 None
        """
        try:
            positions = self.client.futures_position_information()
            for position in positions:
                if position['symbol'] == symbol and float(position['positionAmt']) != 0:
                    side = 'BUY' if float(position['positionAmt']) > 0 else 'SELL'
                    entry_price = float(position['entryPrice'])
                    return {'side': side, 'entryPrice': entry_price}
            return None
        except Exception as e:
            print(f"檢查未平倉交易時出現異常: {e}")
            return None

# class Order:
    def place_order(self, symbol, side, amount):
        """
        執行下單操作。
        :param symbol: 交易對
        :param side: 'BUY' 或 'SELL'
        :param amount: 下單金額 (USDT)
        :return: 下單結果
        """
        try:
            # 獲取交易對的精度限制
            exchange_info = self.client.futures_exchange_info()
            for s in exchange_info['symbols']:
                if s['symbol'] == symbol:
                    step_size = float(s['filters'][2]['stepSize'])  # 數量精度
                    break
            else:
                raise ValueError(f"無法找到交易對 {symbol} 的精度限制")

            # 計算下單數量，假設使用市價單
            price = float(self.client.futures_symbol_ticker(symbol=symbol)['price'])
            quantity = amount / price

            # 調整數量至允許的精度
            precision = int(round(-math.log(step_size, 10), 0))
            quantity = round(quantity, precision)

            if side == 'BUY':
                order = self.client.futures_create_order(
                    symbol=symbol,
                    side='BUY',
                    type='MARKET',
                    quantity=quantity
                )
            elif side == 'SELL':
                order = self.client.futures_create_order(
                    symbol=symbol,
                    side='SELL',
                    type='MARKET',
                    quantity=quantity
                )
            else:
                raise ValueError("無效的下單方向，必須是 'BUY' 或 'SELL'")

            print(f"下單成功: {order}")
            return order
        except Exception as e:
            print(f"下單時出現異常: {e}")
            return None

    def close_position(self, symbol, side):
        """
        執行平倉操作。
        :param symbol: 交易對
        :param side: 'BUY' 或 'SELL'（當前持倉方向）
        :return: 平倉結果
        """
        try:
            # 獲取當前持倉數量
            positions = self.client.futures_position_information()
            for position in positions:
                if position['symbol'] == symbol and float(position['positionAmt']) != 0:
                    quantity = abs(float(position['positionAmt']))  # 持倉數量
                    break
            else:
                print(f"無法找到 {symbol} 的未平倉交易")
                return None

            # 根據當前持倉方向執行平倉
            if side == 'BUY':
                order = self.client.futures_create_order(
                    symbol=symbol,
                    side='SELL',
                    type='MARKET',
                    quantity=quantity
                )
            elif side == 'SELL':
                order = self.client.futures_create_order(
                    symbol=symbol,
                    side='BUY',
                    type='MARKET',
                    quantity=quantity
                )
            else:
                raise ValueError("無效的平倉方向，必須是 'BUY' 或 'SELL'")

            print(f"平倉成功: {order}")
            return order
        except Exception as e:
            print(f"平倉時出現異常: {e}")
            return None

    def get_historical_prices(self, symbol, limit=100):
        """
        使用 Binance 客戶端的 futures_klines 方法獲取最近 limit 根 K 線的收盤價數據。
        """
        print(f"從 Binance API 獲取 {symbol} 的最近 {limit} 根 K 線數據")
        try:
            klines = self.client.futures_klines(symbol=symbol, interval=self.timeframe, limit=limit)
            return [float(kline[4]) for kline in klines]  # 提取收盤價
        except Exception as e:
            print(f"取得 {symbol} 的 K 線數據時出現異常: {e}")
            return []

    def get_account_balance(self):
        """
        使用 Binance API 獲取賬戶餘額。
        """
        print("從 Binance Testnet API 獲取賬戶餘額")
        endpoint = f"{FUTURES_URL}/fapi/v2/account"  # 修正為正確的端點
        timestamp = int(time.time() * 1000)  # 當前時間戳（毫秒）
        query_string = f"timestamp={timestamp}"
        signature = hmac.new(
            self.private_key.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        params = {"timestamp": timestamp, "signature": signature}
        headers = {"X-MBX-APIKEY": self.api_key}

        response = requests.get(endpoint, headers=headers, params=params)  # 使用 GET 方法
        response.raise_for_status()
        data = response.json()

        # 遍歷返回的資產列表，查找 USDT 餘額
        for asset in data["assets"]:
            if asset["asset"] == "USDT":  # 假設使用 USDT 作為交易資金
                return float(asset["walletBalance"])  # 返回 USDT 餘額
        return 0.0  # 如果未找到 USDT，返回 0

    # 使用 Binance API 獲取當前交易量
    def get_current_volume(self, symbol):
        """
        使用 Binance API 獲取當前交易量。
        """
        # print(f"從 Binance Testnet API 獲取 {symbol} 的當前交易量")
        endpoint = f"{FUTURES_URL}/fapi/v1/ticker/24hr"  # 使用 FUTURES_URL 替代 BINANCE_BASE_URL
        params = {"symbol": symbol}
        headers = {"X-MBX-APIKEY": self.api_key}
        response = requests.get(endpoint, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()
        return float(data["volume"])  # 提取交易量