import json

# Qlib：https://github.com/microsoft/qlib


class AlphaFactorGenerator:
    def get_alpha_expression(self):
        fields, names = [], []

        # = KBar ==============================================================================
        fields += [
            "(close-open)/open",
            "(high-low)/open",
            "(close-open)/(high-low+1e-12)",
            "(high-max(open,close))/open",
            "(high-max(open,close))/(high-low+1e-12)",
            "(min(open,close)-low)/open",
            "(min(open,close)-low)/(high-low+1e-12)",
            "(2*close-high-low)/open",
            "(2*close-high-low)/(high-low+1e-12)",
        ]
        # names += [
        #     "KMID",
        #     "KLEN",
        #     "KMID2",
        #     "KUP",
        #     "KUP2",
        #     "KLOW",
        #     "KLOW2",
        #     "KSFT",
        #     "KSFT2",
        # ]
        # = Price ==============================================================================
        feature = ["open", "high", "low", "close", "vwap"]
        windows = range(5)
        for field in feature:
            field = field.lower()
            fields += [f"shift({field},{d})/close" if d != 0 else f"{field}/close" for d in windows]
            # names += [field.upper() + str(d) for d in windows]

        # = Volume ==============================================================================
        fields += [f"shift(volume,{d})/(volume+1e-12)" if d != 0 else f"volume/(volume+1e-12)" for d in windows]
        # names += ["VOLUME" + str(d) for d in windows]

        # = Rolling ==============================================================================
        # Some factor ref: https://guorn.com/static/upload/file/3/134065454575605.pdf
        windows = [5, 10, 20, 30, 60]
        # https://www.investopedia.com/terms/r/rateofchange.asp
        # Rate of change, the price change in the past d days, divided by latest close price to remove unit
        fields += [f"shift(close,{d})/close" for d in windows]
        # names += [f"ROC{d}" for d in windows]

        # The max price for past d days, divided by latest close price to remove unit
        fields += [f"max(high,{d})/close" for d in windows]
        # names += [f"MAX{d}" for d in windows]

        # The low price for past d days, divided by latest close price to remove unit
        fields += [f"min(low,{d})/close" for d in windows]
        # names += [f"MIN{d}" for d in windows]

        # https://www.investopedia.com/ask/answers/071414/whats-difference-between-moving-average-and-weighted-moving-average.asp
        # Simple Moving Average, the simple moving average in the past d days, divided by latest close price to remove unit
        fields += [f"mean(close,{d})/close" for d in windows]
        # names += [f"MA{d}" for d in windows]

        # The standard diviation of close price for the past d days, divided by latest close price to remove unit
        fields += [f"std(close,{d})/close" for d in windows]
        # names += [f"STD{d}" for d in windows]

        # The rate of close price change in the past d days, divided by latest close price to remove unit
        # For example, price increase 10 dollar per day in the past d days, then Slope will be 10.
        fields += [f"slope(close,{d})/close" for d in windows]
        # names += [f"BETA{d}" for d in windows]

        # The R-sqaure value of linear regression for the past d days, represent the trend linear
        fields += [f"rsquare(close,{d})" for d in windows]
        # names += [f"RSQR{d}" for d in windows]

        # The redisdual for linear regression for the past d days, represent the trend linearity for past d days.
        fields += [f"resi(close,{d})/close" for d in windows]
        # names += [f"RESI{d}" for d in windows]

        # The 80% quantile of past d day's close price, divided by latest close price to remove unit
        # Used with MIN and MAX
        fields += [f"quantile(close,{d},0.8)/close" for d in windows]
        # names += [f"QTLU{d}" for d in windows]

        # The 20% quantile of past d day's close price, divided by latest close price to remove unit
        fields += [f"quantile(close,{d},0.2)/close" for d in windows]
        # names += [f"QTLD{d}" for d in windows]

        # Get the percentile of current close price in past d day's close price.
        # Represent the current price level comparing to past N days, add additional information to moving average.
        fields += [f"tsrank(close,{d})" for d in windows]
        # names += [f"TSRANK{d}" for d in windows]

        # Represent the price position between upper and lower resistent price for past d days.
        fields += [f"(close-min(low,{d}))/(max(high,{d})-min(low,{d})+1e-12)" for d in windows]
        # names += [f"RSV{d}" for d in windows]

        # The number of days between current date and previous highest price date.
        # Part of Aroon Indicator https://www.investopedia.com/terms/a/aroon.asp
        # The indicator measures the time between highs and the time between lows over a time period.
        # The idea is that strong uptrends will regularly see new highs, and strong downtrends will regularly see new lows.
        fields += [f"idxmax(high,{d})/{d}" for d in windows]
        # names += [f"IMAX{d}" for d in windows]

        # The number of days between current date and previous lowest price date.
        # Part of Aroon Indicator https://www.investopedia.com/terms/a/aroon.asp
        # The indicator measures the time between highs and the time between lows over a time period.
        # The idea is that strong uptrends will regularly see new highs, and strong downtrends will regularly see new lows.
        fields += [f"idxmin(low,{d})/{d}" for d in windows]
        # names += [f"IMIN{d}" for d in windows]

        # The time period between previous lowest-price date occur after highest price date.
        # Large value suggest downward momemtum.
        fields += [f"(idxmax(high,{d})-idxmin(low,{d}))/{d}" for d in windows]
        # names += [f"IMXD{d}" for d in windows]

        # The correlation between absolute close price and log scaled trading volume
        fields += [f"correlation(close,log(volume+1),{d})" for d in windows]
        # names += [f"CORR{d}" for d in windows]

        # The correlation between price change ratio and volume change ratio
        fields += [f"correlation(close/shift(close,1), log(volume/shift(volume,1)+1), {d})" for d in windows]
        # names += [f"CORD{d}" for d in windows]

        # The percentage of days in past d days that price go up.
        fields += [f"mean(close>shift(close,1), {d})" for d in windows]
        # names += [f"CNTP{d}" for d in windows]

        # The percentage of days in past d days that price go down.
        fields += [f"mean(close<shift(close,1), {d})" for d in windows]
        # names += [f"CNTN{d}" for d in windows]

        # The diff between past up day and past down day
        fields += [f"mean(close>shift(close,1), {d})-mean(close<shift(close,1), {d})" for d in windows]
        # names += [f"CNTD{d}" for d in windows]

        # The total gain / the absolute total price changed
        # Similar to RSI indicator. https://www.investopedia.com/terms/r/rsi.asp
        fields += [f"sum(max(close-shift(close,1),0),{d})/(sum(abs(close-shift(close,1)), {d})+1e-12)" for d in windows]
        # names += [f"SUMP{d}" for d in windows]

        # The total lose / the absolute total price changed
        # Can be derived from SUMP by SUMN = 1 - SUMP
        # Similar to RSI indicator. https://www.investopedia.com/terms/r/rsi.asp
        fields += [f"sum(max(shift(close,1)-close,0), {d})/(sum(abs(close-shift(close,1)), {d})+1e-12)" for d in windows]
        # names += [f"SUMN{d}" for d in windows]

        # The diff ratio between total gain and total lose
        # Similar to RSI indicator. https://www.investopedia.com/terms/r/rsi.asp
        fields += [
            f"(sum(max(close-shift(close,1),0), {d})-sum(max(shift(close,1)-close,0), {d}))/(sum(abs(close-shift(close,1)), {d})+1e-12)" for d in windows
        ]
        # names += [f"SUMD{d}" for d in windows]

        # Simple Volume Moving average: https://www.barchart.com/education/technical-indicators/volume_moving_average
        fields += [f"mean(volume,{d})/(volume+1e-12)" for d in windows]
        # names += [f"VMA{d}" for d in windows]

        # The standard deviation for volume in past d days.
        fields += [f"std(volume,{d})/(volume+1e-12)" for d in windows]
        # names += [f"VSTD{d}" for d in windows]

        # The volume weighted price change volatility
        fields += [f"std(abs(close/shift(close,1)-1)*volume,{d})/(mean(abs(close/shift(close,1)-1)*volume,{d})+1e-12)" for d in windows]
        # names += [f"WVMA{d}" for d in windows]

        # The total volume increase / the absolute total volume changed
        fields += [f"sum(max(volume-shift(volume,1),0), {d})/(sum(abs(volume-shift(volume,1)),{d})+1e-12)" for d in windows]
        # names += [f"VSUMP{d}" for d in windows]

        # The total volume increase / the absolute total volume changed
        # Can be derived from VSUMP by VSUMN = 1 - VSUMP
        fields += [f"sum(max(shift(volume, 1)-volume, 0), {d})/(sum(abs(volume-shift(volume,1)),{d})+1e-12)" for d in windows]
        # names += [f"VSUMN{d}" for d in windows]

        # The diff ratio between total volume increase and total volume decrease
        # RSI indicator for volume
        fields += [
            f"(sum(max(volume-shift(volume,1),0), {d})-sum(max(shift(volume,1)-volume,0),{d}))/(sum(abs(volume-shift(volume,1)),{d})+1e-12)" for d in windows
        ]
        # names += [f"VSUMD{d}" for d in windows]

        result = {}
        for index, field_expression in enumerate(fields, start=1):
            result[f"alpha_158_{index}"] = field_expression

        return result


if __name__ == "__main__":
    alpha_generator = AlphaFactorGenerator()
    alpha_factor_dict = alpha_generator.get_alpha_expression()
    with open(f"./alpha_158.json", "w") as f:
        json.dump(alpha_factor_dict, f)
