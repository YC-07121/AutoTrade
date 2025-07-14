import pandas_ta as ta
import pandas as pd

class ThreeBarReversalStrategy:
    def __init__(self):
        self.atr_period = 14
        self.risk_reward_ratio = 5
    
        
    def check_entry_signal(self,df):
        # 只取最近 25 根，因為要計算成交量門檻（20根平均+標準差） + 最後3根用來判斷
        df = df.iloc[-26:-1].copy()
        # print(df)
        # 計算 ATR
        df["TR"] = df[["High", "Low", "Close"]].apply(
            lambda row: max(row["High"] - row["Low"],
                            abs(row["High"] - row["Close"]),
                            abs(row["Low"] - row["Close"])), axis=1)
        df["ATR"] = df["TR"].rolling(window=self.atr_period).mean()

        # 成交量門檻
        df["vol_avg"] = df["Volume"].rolling(window=10).mean()
        df["vol_std"] = df["Volume"].rolling(window=10).std()
        df["vol_threshold"] = df["vol_avg"] + df["vol_std"]

        # 現在的判斷是看最近第-3、-2、-1根
        c2, o2 = df.iloc[-3]["Close"], df.iloc[-3]["Open"]
        c1, o1 = df.iloc[-2]["Close"], df.iloc[-2]["Open"]
        c0, o0 = df.iloc[-1]["Close"], df.iloc[-1]["Open"]

        h2, h1, h0 = df.iloc[-3]["High"], df.iloc[-2]["High"], df.iloc[-1]["High"]
        l2, l1, l0 = df.iloc[-3]["Low"], df.iloc[-2]["Low"], df.iloc[-1]["Low"]

        atr = df.iloc[-1]["ATR"]
        current_volume = df.iloc[-1]["Volume"]
        vol_threshold = df.iloc[-1]["vol_threshold"]
        
        

        # 判斷三棒型態
        bullish = (                             #上漲訊號
            c2 < o2 and                         #左收紅 (下跌)
            l1 < l2 and h1 < h2 and c1 < o1 and #中低<左低 且 中高<左高 且 中收紅 (持續下跌)
            c0 > o0 and h0 > h2                 #右收綠 且 右高>左高 (上漲綠K吞沒前兩根紅K)
        )

        bearish = (                             #下跌訊號
            c2 > o2 and                         #左收綠 (上漲)
            h1 > h2 and l1 > l2 and c1 > o1 and #中高>左高 且 中低<左低 且 中收綠 (持續上漲)
            c0 < o0 and l0 < l2                 #右收紅 且 右低<左低 (下跌紅K吞沒前兩根綠K)
        )
        # print(df.iloc[-3]["Timestamp"],df.iloc[-2]["Timestamp"],df.iloc[-1]["Timestamp"])
        if bullish:
            # 成交量判斷
            if current_volume < vol_threshold:
                self.risk_reward_ratio = 2
                entry_price = c0
                stop_loss = entry_price - atr
                take_profit = entry_price + atr * self.risk_reward_ratio
                return ("BUY",entry_price,take_profit,stop_loss,self.risk_reward_ratio)
            self.risk_reward_ratio = 5
            entry_price = c0
            stop_loss = entry_price - atr
            take_profit = entry_price + atr * self.risk_reward_ratio
            return ("BUY",entry_price,take_profit,stop_loss,self.risk_reward_ratio)
            
        elif bearish:
            # 成交量判斷
            if current_volume < vol_threshold:
                self.risk_reward_ratio = 2
                entry_price = c0
                stop_loss = entry_price + atr
                take_profit = entry_price - atr * self.risk_reward_ratio
                return ("SELL",entry_price,take_profit,stop_loss,self.risk_reward_ratio)
            self.risk_reward_ratio = 5
            entry_price = c0
            stop_loss = entry_price + atr
            take_profit = entry_price - atr * self.risk_reward_ratio
            return ("SELL",entry_price,take_profit,stop_loss,self.risk_reward_ratio)
            
        else:
            return None