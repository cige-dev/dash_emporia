from datetime import datetime  
from dateutil.relativedelta import relativedelta  
from src.emporia_conection import data_extract
from sqlalchemy import create_engine  
import pandas as pd
import time, glob, os


def checking_data(client):   
    device_name, data = ('', pd.DataFrame(columns=['Time Bucket']))
    current_date = datetime.fromtimestamp(time.time())
    start_date = datetime.fromtimestamp(time.time()) - relativedelta(years=1)
    client_on_db = [i for i in glob.glob('db/*.db') if client.lower() in i]
    if len(client_on_db)==0:
        data_concat = []
        for i in range(4):
            start_interval = (start_date + relativedelta(months=3*i)).timestamp()
            end_interval = (start_date + relativedelta(months=3*(i+1)) if i<3 else current_date).timestamp()
            data, device_name = data_extract(client, start_interval, end_interval)
            data_concat.append(data)
        data = pd.concat(data_concat)
        if len(data)==0: pass
        else:
            engine = create_engine(f'sqlite:///db/{device_name.lower()}.db')
            data.to_sql(f'{device_name.lower()}', con=engine, if_exists='replace', index=False)
    else:
        data_concat = pd.DataFrame()
        engine = create_engine(f'sqlite:///{client_on_db[0]}')
        data = pd.read_sql(f"{client_on_db[0][3:-3]}", con=engine)  
        data['Time Bucket'] = [pd.to_datetime(t, format='%Y-%m-%d').date() for t in data['Time Bucket']]
        last_date = data['Time Bucket'].values[-1]
        last_date = datetime(last_date.year, last_date.month, last_date.day)  
        try:
            data_concat, device_name = data_extract(cliente=client, 
                                                    start_interval=last_date.timestamp(), 
                                                    end_interval=current_date.timestamp())
            data = pd.concat([data.iloc[:-1],data_concat])
            data.to_sql(f'{device_name.lower()}', con=engine, if_exists='replace', index=False)
        except: 
            engine.dispose()  
            os.remove(client_on_db[0])  
    return device_name, data