import pandas_ta as ta
import pandas as pd
import Account as op

class BinanceStrategy:
    def __init__(self, symbol='BTCUSDT', timeframe='30m', limit=100):
        self.exchange = op.Operate(symbol,timeframe,limit)

    def fetch_data(self):
        print("取得資料中...")
        self.df = self.exchange.getFuturesKlines()
        print(self.exchange.nowFuturesPrice())
        return self.df

    def add_indicators(self):
        print("正在套用技術指標...")

        try:
            self.df["EMA"] = ta.ema(self.df["Close"], length=9)
            self.df["DEMA"] = ta.dema(self.df["Close"], length=5)
            macd = ta.macd(self.df["Close"],fast=12,slow=30,signal=9)
            macd.columns = ["MACD", "MACDh", "MACDs"]
            self.df = pd.concat([self.df, macd], axis=1)

            self.df["RSI"] = ta.rsi(self.df["Close"],length=21)
            self.df["OBV"] = ta.obv(close=self.df["Close"], volume=self.df["Volume"])

            stoch = ta.stochrsi(self.df["Close"],length=7)
            stoch.columns = ["STOCHRSIk", "STOCHRSId"]
            self.df = pd.concat([self.df, stoch], axis=1)

        except Exception as e:
            print("套用技術指標時出現異常:", e)

        return self.df
    
    

    # def evaluate_strategy(self):
        # 新策略
        # 想法:
        # 進場訊號:
        # 1.RSI結合OBV
        # 2.MACD背離結合
        # 3.三均線交叉策略
        # 4.斐波那契結合支撐壓力位策略
        # 出場訊號
        # 止損出場:入場價格結合ATR
        # 止盈出場:買入時ATR數值*2 加上價格

    def run(self):
        print("執行中...")
        self.df = self.fetch_data()
        print("資料取得完成")
        self.df = self.add_indicators()
        print("技術指標分析完成")
        prediction = self.evaluate_strategy()
        print(f"Predicted 10-minute movement: {prediction}")
        return prediction


