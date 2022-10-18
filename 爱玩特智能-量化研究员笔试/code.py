import pymysql 
import pandas as pd
import matplotlib.pyplot as plt
from functools import reduce
import numpy as np
import statsmodels.api as sm

# 问题（1）：连接数据库
conn = pymysql.Connect(
    host = 'bj-cdb-3gfxha84.sql.tencentcdb.com', 
    port = 59970,  
    user = 'root',  
    passwd = 'ainvest_test1', 
    db = 'test', 
    charset = 'utf8'
    )

# 问题（2）画出时间-用户数的走势图
sql = 'SELECT * FROM account_balance;'
data = pd.read_sql(sql, conn)
time_user_number_dict =dict(data.As_Of_Date.value_counts())
time_user_number = sorted(time_user_number_dict.items(), key=lambda item:item[0])
x = range(len(time_user_number))
y = list(dict(time_user_number).values())
plt.plot(x,y,'s-',color = 'r')#s-:方形
plt.xlabel("As_Of_Date")#横坐标名字
plt.ylabel("numbers")#纵坐标名字
plt.show()

# 问题（3）计算每个用户每天的投资回报率。
sql = 'SELECT  As_Of_Date,ID,Total_account FROM account_balance;'
data_history = pd.read_sql(sql, conn)

user_list =  list(set(data_history.ID))
user_return_rate = {}
for user in user_list:
    user_data = data_history[data_history['ID'] ==user]
    # 按时间排序
    user_data.sort_values(by='As_Of_Date')
    # 计算投资回报率：(后一行的总金额/前一行的总金额)-1
    return_rate =list((user_data['Total_account'].shift(periods=-1, axis=0)/user_data['Total_account']).apply(lambda x: x-1))
    # 按时间顺序存储每个用户每天的投资回报率
    user_return_rate[user] = return_rate[:-1]

# 问题（4）计算每个用户每天的累计回报率
for user,rate_list in user_return_rate.items():
    # 累计回报率：每天的回报率+1后，再全部求乘积
    reduce_rate = reduce(lambda x,y:x*y,[x+1 for x in rate_list ])
    print('用户ID{}的累计回报率为={}'.format(user,reduce_rate))


# 问题（5）计算描述性统计
# 年华回报率
sharpe_ratio_dict = {}
for user,rate_list in user_return_rate.items():
    # 年化回报率
    year_return_rate = np.mean(rate_list)*252
    # 年化波动率
    year_volatility = np.std(rate_list,ddof=1)* np.sqrt(252)
    # 夏普比率
    sharpe_ratio = year_return_rate/year_volatility
    sharpe_ratio_dict[user] = sharpe_ratio

# 输出夏普比率最高和最低的用户
sharpe_ratio_dict_sorted= dict(sorted(sharpe_ratio_dict.items(), key=lambda item:item[1]))
print('夏普比率最低的用户是{},夏普比率为{}'.format(list(sharpe_ratio_dict_sorted.keys())[0],list(sharpe_ratio_dict_sorted.values())[0]))
print('夏普比率最高的用户是{},夏普比率为{}'.format(list(sharpe_ratio_dict_sorted.keys())[-1],list(sharpe_ratio_dict_sorted.values())[-1]))


# 问题（6）简单线性回归
# 输出前95%的最后一天日期和后5%最后一天日期。
user_data = data_history[data_history['ID'] ==user_list[0]]
# 按时间排序
user_data.sort_values(by='As_Of_Date')
# 前95%的数据跨度天数
data_len = int(len(rate_list)*0.95)
print('前95%的最后一天日期是{}'.format(user_data['As_Of_Date'].iloc[data_len-1]))
print('后5%的最后一天日期是{}'.format(user_data['As_Of_Date'].iloc[len(user_data)-1]))
X = []
Y = []
for user,rate_list in user_return_rate.items():
    # 第一步计算样本前95%的年化回报率
    x_year_return_rate = np.mean(rate_list[:data_len])*252
    # 第二步计算样本后5%的年化回报率
    y_year_return_rate = np.mean(rate_list[data_len+1:])*252
    X.append(x_year_return_rate)
    Y.append(y_year_return_rate)


# 第三步，线性回归分析
X = sm.add_constant(X) # 若模型中有截距，必须有这一步
model = sm.OLS(Y, X).fit() # 构建最小二乘模型并拟合
print(model.summary()) # 输出回归结果

conn.close()
