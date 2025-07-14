from binance.client import Client
import pandas as pd
from Config import API_KEY, PRIVATE_KEY  # 使用絕對導入 PRIVATE_KEY

# 初始化客戶端

class Klines:

    def __init__(self, symbol, timeframe, limit):
        self.symbol = symbol
        self.timeframe = timeframe
        self.limit = limit
        self.api_key = API_KEY
        self.private_key = PRIVATE_KEY
        self.client = Client(self.api_key, self.private_key) 
    
    def getSpotKlines(self) :
        print("正在取得K棒資料...")
        # 獲取 BTCUSDT 的現貨 K 線數據
        if self.timeframe=="1s":
            klines = self.client.get_klines(symbol=self.symbol, interval=Client.KLINE_INTERVAL_1SECOND, limit=self.limit)
        elif self.timeframe=="1m":
            klines = self.client.get_klines(symbol=self.symbol, interval=Client.KLINE_INTERVAL_1MINUTE, limit=self.limit)
        elif self.timeframe=="5m":
            klines = self.client.get_klines(symbol=self.symbol, interval=Client.KLINE_INTERVAL_5MINUTE, limit=self.limit)
        elif self.timeframe=="15m":
            klines = self.client.get_klines(symbol=self.symbol, interval=Client.KLINE_INTERVAL_15MINUTE, limit=self.limit)
        elif self.timeframe=="30m":
            klines = self.client.get_klines(symbol=self.symbol, interval=Client.KLINE_INTERVAL_30MINUTE, limit=self.limit)
        elif self.timeframe=="1h":
            klines = self.client.get_klines(symbol=self.symbol, interval=Client.KLINE_INTERVAL_1HOUR, limit=self.limit)
        elif self.timeframe=="4h":
            klines = self.client.get_klines(symbol=self.symbol, interval=Client.KLINE_INTERVAL_4HOUR, limit=self.limit)
        elif self.timeframe=="1d":
            klines = self.client.get_klines(symbol=self.symbol, interval=Client.KLINE_INTERVAL_1DAY, limit=self.limit)
        elif self.timeframe=="1w":
            klines = self.client.get_klines(symbol=self.symbol, interval=Client.KLINE_INTERVAL_1WEEK, limit=self.limit)
        elif self.timeframe=="1M":
            klines = self.client.get_klines(symbol=self.symbol, interval=Client.KLINE_INTERVAL_1MONTH, limit=self.limit)
        # 將數據轉換為 DataFrame
        df = pd.DataFrame(klines, columns=['Timestamp', 'Open', 'High', 'Low', 'Close', 'Volume', 'Close_time', 'Quote_asset_volume', 'Number_of_trades', 'Taker_buy_base_asset_volume', 'Taker_buy_quote_asset_volume', 'Ignore'])
        # print(df.head(3))
        # 轉換時間戳
        df['Timestamp'] = pd.to_datetime(df['Timestamp'], unit='ms')
        df[['Open', 'High', 'Low', 'Close', 'Volume', 'Close_time', 'Quote_asset_volume', 'Number_of_trades', 'Taker_buy_base_asset_volume', 'Taker_buy_quote_asset_volume', 'Ignore']] = df[['Open', 'High', 'Low', 'Close', 'Volume', 'Close_time', 'Quote_asset_volume', 'Number_of_trades', 'Taker_buy_base_asset_volume', 'Taker_buy_quote_asset_volume', 'Ignore']].astype('float')
        # print(type(df['Open'][0]))
        # 打印前幾行數據
        # print(df.head(3))
        return df
    
    def getFuturesKlines(self):
        print("正在取得【合約】K棒資料...")
        
        interval_map = {
            "1s": Client.KLINE_INTERVAL_1MINUTE,   # Futures 不支援 1s
            "1m": Client.KLINE_INTERVAL_1MINUTE,
            "5m": Client.KLINE_INTERVAL_5MINUTE,
            "15m": Client.KLINE_INTERVAL_15MINUTE,
            "30m": Client.KLINE_INTERVAL_30MINUTE,
            "1h": Client.KLINE_INTERVAL_1HOUR,
            "4h": Client.KLINE_INTERVAL_4HOUR,
            "1d": Client.KLINE_INTERVAL_1DAY,
            "1w": Client.KLINE_INTERVAL_1WEEK,
            "1M": Client.KLINE_INTERVAL_1MONTH,
        }

        if self.timeframe not in interval_map:
            raise ValueError(f"不支援的時間區間: {self.timeframe}")

        # 取期貨K線資料
        try :
            klines = self.client.futures_klines(
                symbol=self.symbol,
                interval=interval_map[self.timeframe],
                limit=self.limit
            )
        except Exception as e:
            print("取得K線時出現異常")
            print(e)
            return None


        # 整理成 DataFrame
        print("正在整理K棒資料")
        df = pd.DataFrame(klines, columns=[
            'Timestamp', 'Open', 'High', 'Low', 'Close', 'Volume', 'Close_time',
            'Quote_asset_volume', 'Number_of_trades', 'Taker_buy_base_asset_volume',
            'Taker_buy_quote_asset_volume', 'Ignore'
        ])
        df['Timestamp'] = pd.to_datetime(df['Timestamp'], unit='ms', utc=True)
        df['Timestamp'] = df['Timestamp'].dt.tz_convert('Asia/Taipei')
        cols_to_float = [
            'Open', 'High', 'Low', 'Close', 'Volume',
            'Quote_asset_volume', 'Taker_buy_base_asset_volume',
            'Taker_buy_quote_asset_volume'
        ]
        df[cols_to_float] = df[cols_to_float].astype(float)

        return df
    
    def nowFuturesPrice(self):
        try:
            price_info = self.client.futures_symbol_ticker(symbol=self.symbol)
            return float(price_info["price"])
        except Exception as e:
            print("❌ 無法取得當前合約價格:", e)
            return None
