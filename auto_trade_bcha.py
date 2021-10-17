import pyupbit
import time
import datetime
import pandas as pd
import numpy as np

# 로그인
access = "HLCgvVEaczRksuvGO8Xt50JWHtUvxeHnm5vR38De"
secret = "bau5te5LhXXvhNxNbFxcz7fMHDCxce8yHE9QrJxE"

upbit = pyupbit.Upbit(access, secret)
print("Login OK")

# 총 매수 할 원화, 분할 매수 비율
total = 100000
rate30 = 0.3
rate40 = 0.4
rate_minus = 0.95

# 시간 간격
interval = "day"
# interval = "minute240"
# 1일 단위는 "day", 분단위는 "minute240, minute60, minute 30"등을 지정할 수 있습니다.

# ticker, k, currency
ticker = "KRW-DAWN"
currency = "DAWN"
k = 0.7


def get_target_price(ticker, interval, k):  # 변동성 돌파 전략으로 매수 목표가 정하기
    df = pyupbit.get_ohlcv(ticker, interval=interval, count=2)
    target_price = df.iloc[0]['close'] + (df.iloc[0]['high'] - df.iloc[0]['low']) * k
    return target_price


def get_start_time(ticker, interval):  # 시작 시간 조회
    df = pyupbit.get_ohlcv(ticker, interval=interval, count=1)
    start_time = df.index[0]
    return start_time


#test
def get_current_price(ticker):
    value = pyupbit.get_orderbook(ticker)[0]["orderbook_units"][0]["ask_price"]
    return value


def get_balance(currency):  # 잔고 조회
    balances = upbit.get_balances()
    for b in balances:
        if b['currency'] == currency:
            if b['balance'] is not None:
                return float(b['balance'])
            else:
                return 0


def get_buy_average(currency):  # 매수평균가
    balances = upbit.get_balances()
    for b in balances:
        if b['currency'] == currency:
            if b['avg_buy_price'] is not None:
                return float(b['avg_buy_price'])
            else:
                return 0


def get_trade_time(ticker):  # 최근 거래 채결 날짜 가져오기
    df = pd.DataFrame(upbit.get_order(ticker, state="done"))
    trade_done = df.iloc[0]["created_at"]
    trade_done_time = datetime.datetime.strptime(trade_done[:-6], "%Y-%m-%dT%H:%M:%S")
    return trade_done_time


def get_ror(k=0.5):  # 최고의 k값을 구하는 함수
    df = pyupbit.get_ohlcv(ticker, count=7)
    df['range'] = (df['high'] - df['low']) * k
    df['target'] = df['open'] + df['range'].shift(1)

    df['ror'] = np.where(df['high'] > df['target'],
                         df['close'] / df['target'],
                         1)

    ror = df['ror'].cumprod()[-2]
    return ror


##########################################################################################################


# 자동 매매 무한반복
while True:

    # 시간 설정
    start_time = get_start_time(ticker, interval)
    now = datetime.datetime.now()
    end_time = start_time + datetime.timedelta(days=1) - datetime.timedelta(seconds=5)
    # end_time = start_time + datetime.timedelta(minutes=240) - datetime.timedelta(seconds=5)

    # 매매 시작
    if start_time < now < end_time:
        target_price = get_target_price(ticker, interval, k)
        print("Start: %s" % start_time)
        print("End: %s" % end_time)
        print("Target price: %d" % target_price)

        i = 0
        while i < 3:
            now = datetime.datetime.now()
            current_price = get_current_price(ticker)
            time.sleep(0.5)

            # 매수 1차
            if i == 0 and (target_price - 50) <= current_price < (target_price + 100):
                upbit.buy_market_order(ticker, total * rate30)
                time.sleep(1)
                buy_average = get_buy_average(currency)
                threeCount = buy_average * 0.03
                result = buy_average + threeCount
                i += 1
                print("%dst Buy OK" % (i))
                if result <= get_current_price(ticker):
                    time.sleep(60)
                    coin = get_balance(currency)
                    upbit.sell_market_order(ticker, coin)
                    time.sleep(2)
                    break

                # 매수 2차
            if i == 1 and current_price < buy_average * rate_minus:
                upbit.buy_market_order(ticker, total * rate30)
                time.sleep(1)
                buy_average = get_buy_average(currency)
                threeCount = buy_average * 0.06
                result = buy_average + threeCount
                i += 1
                print("%dnd Buy OK" % (i))
                if result <= get_current_price(ticker):
                    time.sleep(60)
                    coin = get_balance(currency)
                    upbit.sell_market_order(ticker, coin)
                    time.sleep(2)
                    break

            # 매수 3차
            if i == 2 and current_price < buy_average * rate_minus:
                upbit.buy_market_order(ticker, total * rate40)
                time.sleep(1)
                buy_average = get_buy_average(currency)
                threeCount = buy_average * 0.09
                result = buy_average + threeCount
                i += 1
                print("%drd Buy OK" % (i))
                if result <= get_current_price(ticker):
                    time.sleep(60)
                    coin = get_balance(currency)
                    upbit.sell_market_order(ticker, coin)
                    time.sleep(2)
                    break

            if now > end_time:
                break


    elif now > end_time:
        coin = get_balance(currency)
    upbit.sell_market_order(ticker, coin)
    k = round((np.argmax(list(map(lambda i: get_ror(i), np.arange(0.1, 1.0, 0.1)))) + 1) * 0.1, 1)
    total = get_balance("KRW")
    time.sleep(2)
    print("Sell OK")
