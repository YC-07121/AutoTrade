"""
#TODO 成交量歸納分析
#TODO 收益最大化下單數量計算
#TODO 最大盈虧比統計
#TODO ETH評估
#ETH 評估不適用TBRS
#TODO 新策略
"""

import pandas as pd
from Klines import Klines
from TBRS_for_BT import ThreeBarReversalStrategy

class BacktestSimulator:
    def __init__(self):
        self.symbol = "BTCUSDT"
        self.klines = Klines(self.symbol, '30m', 1000)
        self.strategy = ThreeBarReversalStrategy(self.klines)

    def ThreeBarReversalSimulate(self):
        print("開始 Three Bar Reversal 回測模擬...")
        output_file = "three_bar_backtest_with_result.csv"

        df = self.strategy.fetch_data()
        results = []

        for i in range(30, len(df) - 1):
            # print(df.iloc[i]["Timestamp"])
            window_df = df.iloc[i - 27:i+1].copy()
            # print(window_df.iloc[-1]["Timestamp"])
            # break
            signal = self.strategy.check_entry_signal(window_df)
            if signal:
                direction, entry_price, take_profit, stop_loss, risk_ratio = signal
                entry_time = df.iloc[i]["Timestamp"]

                result = "timeout"
                exit_price = df.iloc[i]["Close"]
                exit_time = df.iloc[i]["Timestamp"]

                for j in range(i, len(df)):
                    high = df.iloc[j]["High"]
                    low = df.iloc[j]["Low"]

                    if direction == "BUY":
                        if low <= stop_loss:
                            result = "stop_loss"
                            exit_price = stop_loss
                            exit_time = df.iloc[j]["Timestamp"]
                            break
                        elif high >= take_profit:
                            result = "take_profit"
                            exit_price = take_profit
                            exit_time = df.iloc[j]["Timestamp"]
                            break
                    elif direction == "SELL":
                        if high >= stop_loss:
                            result = "stop_loss"
                            exit_price = stop_loss
                            exit_time = df.iloc[j]["Timestamp"]
                            break
                        elif low <= take_profit:
                            result = "take_profit"
                            exit_price = take_profit
                            exit_time = df.iloc[j]["Timestamp"]
                            break

                pnl = (exit_price / entry_price) - 1 if direction == "BUY" else (entry_price / exit_price) - 1
                pnl_str = f"{round(pnl * 100, 2)}%"

                results.append({
                    "entry_time": entry_time,
                    "direction": direction,
                    "risk_ratio": risk_ratio,
                    "entry_price": entry_price,
                    "take_profit": take_profit,
                    "stop_loss": stop_loss,
                    "exit_time": exit_time,
                    "exit_price": exit_price,
                    "result": result,
                    "pnl": pnl_str
                })

        result_df = pd.DataFrame(results)
        result_df.to_csv(output_file, index=False)
        print(f"✅ 回測完成，已輸出至 {output_file}")


    def count_avg(df, bars=20):
        """
        計算前 bars 根 K 棒的成交量平均值

        參數:
            df (pd.DataFrame): 包含 K 線資料的 DataFrame，需包含 'Volume' 欄位
            bars (int): 要計算的 K 棒數量

        回傳:
            float: 成交量平均值
        """
        if len(df) < bars:
            raise ValueError(f"資料不足，至少需要 {bars} 根 K 棒")
        return df["Volume"].iloc[-bars:].mean()
