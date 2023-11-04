from api import data_api
from transforming import transforming
from dash.dependencies import Input, Output, State
from dateutil.relativedelta import relativedelta
from datetime import datetime
from dash import dcc, html
from io import BytesIO
import requests, base64
import pandas as pd
import dash, time


external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
server = app.server
url = "https://media.licdn.com/dms/image/C560BAQEkLah7iU0OXg/company-logo_200_200/0/1622576378267?e=1701907200&v=beta&t=jHOKiWYubvJbIHNss3cvWPgbf5Rv_427P9tq7jcd5pY"
response = requests.get(url)
image_bytes = BytesIO(response.content)
encoded_image = base64.b64encode(image_bytes.read()).decode("utf-8")
date_range = pd.date_range(start=datetime.now()-relativedelta(days=60),end=datetime.now()-relativedelta(days=1))
app.layout = html.Div([
    html.Img(src='data:image/png;base64,{}'.format(encoded_image), style={'width':'12.5%', 'float':'left', 'margin-left':'150px', 'margin-top':'-35px'}),
    dcc.Input(id='email', type='email', placeholder='Ingrese su correo'),
    dcc.Input(id='client', type='text', placeholder='Ingrese el monitor'),
    dcc.DatePickerRange(
            id='my-date-picker-range',
            min_date_allowed=date_range.min(),
            max_date_allowed=date_range.max(),
            initial_visible_month=(datetime.now()-relativedelta(months=1)).date(),
            start_date = (datetime.now()-relativedelta(months=1)-relativedelta(days=1)).date(),
            end_date = date_range.max()),
    html.Div(id='text_info'),
    html.Div(id='title_output'),
    html.Div(id='dash_output'),
], style={'width':'100%', 'text-align':'center'})
@app.callback(
    Output('text_info', 'children'),
    Output('title_output', 'children'),
    Output('dash_output', 'children'),
    Input('email', 'value'),
    Input('client', 'value'),
    Input('my-date-picker-range', 'start_date'),
    Input('my-date-picker-range', 'end_date')
)
def update_output(email, client, start_date, end_date):
    if email in ['hsoto@cigepty.com', 'info@cigepty.com'] and client:
        start_time = time.time()
        if email in ['info@cigepty.com', 'hsoto@cigepty.com']:
            device_name, data, data_hist = data_api(client)
            start_date = pd.Timestamp(start_date).to_pydatetime().date()
            end_date = pd.Timestamp(end_date).to_pydatetime().date()
            title_output, dash_output = transforming(device_name, data, data_hist, start_date, end_date)
            execution_time = round(time.time() - start_time, 2)
            return f'Tiempo de ejecución: {execution_time}s',title_output, dash_output
        else:
            return 'Acceso denegado, verifica tus credenciales.', None, None
    else:
        return 'Tiempo estimado en generar informe por primera vez: 1.5min', None, None
if __name__ == '__main__':
    app.run_server(debug=True)
