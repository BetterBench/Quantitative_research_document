import pandas as pd 
from datetime import timedelta,datetime
# 读取文件
dst = pd.read_csv('dst.csv')
T0  = pd.read_csv('T0.csv')

# 提取dts中的InstrumentID和目标底仓股数，并映射到T)表中
df_dst = dst[1:].reset_index()
df_dst['InstrumentID'] = df_dst['T0EndTime 14:40:00'].map(lambda x:x.split()[0])
df_dst['TradedVol'] = df_dst['T0EndTime 14:40:00'].map(lambda x:x.split()[1])
dst_dict = dict(zip(list(df_dst['InstrumentID']),list(df_dst['TradedVol'])))
T0['target'] = df_dst['InstrumentID'].map(dst_dict)

# 计算是否平仓或开仓
def get_info(s,n,m):
    # 小于目标底仓还卖出，则是开仓
    if s=='S' and int(n)<int(m):
        return 1
    else:
    # 平仓
        return 0
T0['是否开仓'] = T0.apply(lambda row :get_info(row['Direction'],row['TradedVol'],row['target']),axis=1)
T0_result = []
open_T0 = T0[T0['是否开仓']==1]
unwin_T0 = T0[T0['是否开仓']==0]
for i  in range(len(unwin_T0)):
    # 计算当前时间
    time_now = datetime.strptime(unwin_T0['TradeTime'].iloc[i], "%H:%M:%S")
    last_time = time_now + timedelta(minutes=30)
    tradedVol_unwin = unwin_T0['TradedVol'].iloc[i]
    for j in range(len(open_T0)):
        tmp_T0 = []
        tiem_now2 = datetime.strptime(open_T0['TradeTime'].iloc[j], "%H:%M:%S")
        tradedVol_open_T0 = open_T0['TradedVol'].iloc[j]
        # 匹配30分钟内的开仓样本，如果匹配成功，计算交易价格差值，并乘以交易数量，再计算所有匹配成功的总和，即为T0
        if time_now<=tiem_now2<=last_time and tradedVol_open_T0==tradedVol_unwin:
            gain = open_T0['TradePrice'].iloc[j] -unwin_T0['TradePrice'].iloc[i]
            tmp_T0.append(gain*tradedVol_open_T0)
    T0_result.append(sum(tmp_T0))

print(T0_result)
# [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, -113.9999999999997, 0, 0]