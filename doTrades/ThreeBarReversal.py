import pandas as pd

class ThreeBarReversal:
    def __init__(self, atr_period=14, risk_reward_ratio=5):
        self.atr_period = atr_period
        self.risk_reward_ratio = risk_reward_ratio

    def apply(self, df):
        df = df.copy()

        # 計算 ATR
        df["TR"] = df[["High", "Low", "Close"]].apply(
            lambda row: max(row["High"] - row["Low"],
                            abs(row["High"] - row["Close"]),
                            abs(row["Low"] - row["Close"])), axis=1)
        df["ATR"] = df["TR"].rolling(window=self.atr_period).mean()

        # 計算成交量的判斷基準：過去 20 根 K 棒的平均 + 一倍標準差
        df["vol_avg"] = df["Volume"].rolling(window=20).mean()
        df["vol_std"] = df["Volume"].rolling(window=20).std()
        df["vol_threshold"] = df["vol_avg"] + df["vol_std"]

        for i in range(21, len(df)):
            atr = df.iloc[i]["ATR"]
            if pd.isna(atr):
                continue

            # 成交量條件（此根 K 棒的成交量需大於平均 + 1倍標準差）
            if df.iloc[i]["Volume"] < df.iloc[i]["vol_threshold"]:
                continue

            c0, o0 = df.iloc[i]["Close"], df.iloc[i]["Open"]
            c1, o1 = df.iloc[i - 1]["Close"], df.iloc[i - 1]["Open"]
            c2, o2 = df.iloc[i - 2]["Close"], df.iloc[i - 2]["Open"]

            h0, h1, h2 = df.iloc[i]["High"], df.iloc[i - 1]["High"], df.iloc[i - 2]["High"]
            l0, l1, l2 = df.iloc[i]["Low"], df.iloc[i - 1]["Low"], df.iloc[i - 2]["Low"]

            bullish = (
                c2 < o2 and
                l1 < l2 and h1 < h2 and c1 < o1 and
                c0 > o0 and h0 > h2
            )

            bearish = (
                c2 > o2 and
                h1 > h2 and l1 > l2 and c1 > o1 and
                c0 < o0 and l0 < l2
            )

            if bullish or bearish:
                entry_price = c0
                stop_loss = entry_price - atr if bullish else entry_price + atr
                take_profit = entry_price + atr * self.risk_reward_ratio if bullish else entry_price - atr * self.risk_reward_ratio
                signal = 1 if bullish else -1
                return signal, entry_price, stop_loss, take_profit

        return 0, None, None, None
