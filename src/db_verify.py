from datetime import datetime  
from dateutil.relativedelta import relativedelta  
from src.emporia_conection import data_extract
import pandas as pd
import time, glob


def checking_data(client):   
    device_name, data = ('', pd.DataFrame(columns=['Time Bucket']))
    current_date = datetime.fromtimestamp(time.time())
    start_date = datetime.fromtimestamp(time.time()) - relativedelta(years=1)
    client_on_db = [i for i in glob.glob('db/*.csv') if client.lower() in i]
    if len(client_on_db)==0:
        try:
            data_concat = []
            for i in range(4):
                start_interval = (start_date + relativedelta(months=3*i)).timestamp()
                end_interval = (start_date + relativedelta(months=3*(i+1)) if i<3 else current_date).timestamp()
                data, device_name = data_extract(client.lower(), start_interval, end_interval)
                data_concat.append(data)
            data = data.merge(data_concat, on='Time Bucket')
            data.to_csv(f'db/{device_name.lower()}.csv',index=False)
        except: pass
    else:
        data = pd.read_csv(f"{client_on_db[0].lower()}")
        data['Time Bucket'] = [pd.to_datetime(t, format='%Y-%m-%d').date() for t in data['Time Bucket']]
        time_diff = current_date-pd.to_datetime(data['Time Bucket'].values[-1])
        if 0<time_diff.days<60:
            start_interval = (start_date + relativedelta(months=9)).timestamp()
            data_concat, device_name_ = data_extract(client.lower(), start_interval, current_date.timestamp())
            data = data.merge(data_concat, on='Time Bucket')
            data.to_csv(f'db/{device_name.lower()}.csv', index=False)
    return device_name, data