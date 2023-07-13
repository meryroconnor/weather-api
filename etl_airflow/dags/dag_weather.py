from datetime import timedelta, datetime
from weather_pckg.api_utils import request_forecast
from weather_pckg.redshift_utils import load_to_redshift,conn_redshift
from weather_pckg.transform import calculate_humidity_ratio,calculate_mean_avg_humidity
from weather_pckg.smtp_utils import get_login

import pandas as pd
import numpy as np
import os

# Envio de mail
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


#Airflow
from airflow import DAG
# Operadores
from airflow.operators.python_operator import PythonOperator

dag_path = os.getcwd()  # path original.. home en Docker


# argumentos por defecto para el DAG
default_args = {
    'owner': 'MariaRO',
    'start_date': datetime(2023, 6, 19),
    'retries': 5,
    'retry_delay': timedelta(minutes=5)
}

BC_dag = DAG(
    dag_id='dag_weather',
    default_args=default_args,
    description='Obtiene el pronostico del dia ejecutado',
    schedule_interval='0 6 * * *',
    catchup=False
)


# funcion de extraccion de datos
def extract_data(exec_date):
    df_list = []
    print("*"*15)
    print(exec_date)
    #end = datetime.strptime(exec_date, '%Y-%m-%d').date()
    end = datetime.strptime(exec_date.split("T")[0], '%Y-%m-%d').date() + timedelta(days=1)
    start = end - timedelta(days=4)

    while (start <= end):
        row = request_forecast(start)
        df_list.append(row)
        start = start + timedelta(days=1)

    df = pd.concat(df_list)
    df.to_csv(dag_path+f'/raw_data/{exec_date}.csv', index=False)

# Funcion de transformacion en tabla
def transform_data(exec_date):

    df = pd.read_csv(dag_path+f'/raw_data/{exec_date}.csv')

    df["description"] = df["description"].str.lower()
    df["cloud_coverage"] = np.where(df["description"].str.contains("sunny"), 0, 1)
    df["rain"] = np.where(df["totalprecip_mm"] > 0, 1, 0)
    df['rain_tomorrow'] = df['rain'].shift(-1)

    df['mean_avghumidity_3days'] = calculate_mean_avg_humidity(df)
    df['humidity_ratio'] = calculate_humidity_ratio(df)

    df = df[df["date"] == exec_date]
    df.to_csv(dag_path+f'/processed_data/{exec_date}.csv', index=False)


# Funcion conexion a redshift
def upload_data(exec_date):
    df = pd.read_csv(dag_path+f'/processed_data/{exec_date}.csv')
    conn_db_coder = conn_redshift(dag_path+"/.creds/pwd_coder.txt")
    load_to_redshift(conn=conn_db_coder, table_name="forecast", dataframe=df)

def send_email(exec_date):
    # Email configuration
    sender_email = 'meryroconnor@gmail.com'
    receiver_email = 'meryroconnor@hotmail.com'

    smtp_port, smtp_server, smtp_username, smtp_password = get_login(dag_path+"/.creds/smtp_pwd.txt")

    # Create message object
    message = MIMEMultipart()
    message['From'] = sender_email
    message['To'] = receiver_email
    message['Subject'] = f'Weather Data for {exec_date}'

    # Load weather data
    df = pd.read_csv(dag_path + f'/processed_data/{exec_date}.csv')

    # Create HTML content for the email body
    html_content = f'''
        <html>
    <body style="font-family: Arial, sans-serif; background-color: #f7f7f7; margin: 0; padding: 0;">
      <table style="max-width: 600px; margin: 0 auto; background-color: #ffffff;" cellpadding="0" cellspacing="0">
        <tr>
          <td>
            <div style="padding: 20px; background-color: #333333; color: #ffffff; text-align: center;">
              <h1 style="margin: 0;">Informe Climático</h1>
              <p style="margin: 5px 0 0;">Fecha: {exec_date}</p>
            </div>
          </td>
        </tr>
        <tr>
          <td>
            <div style="padding: 20px;">
              <h2 style="margin: 0;">Buenos Aires</h2>
              <p style="margin-top: 5px;">Toda los datos que necesitas saber hoy!</p>
            </div>
          </td>
        </tr>'''''
    # Convert DataFrame to HTML with to_html()
    df_html = df.to_html()
    modified_html = df_html.replace('<table', '<table style="width: 100%; border-collapse: collapse;"')
    modified_html = modified_html.replace('<th>',
                                          '<th style="padding: 8px; border: 1px solid #dddddd; text-align: left;">')
    modified_html = modified_html.replace('<td>', '<td style="padding: 8px; border: 1px solid #dddddd;">')

    html_content += f'<tr><td>{modified_html}</td></tr>'
    html_content += '''<tr>
              <td>
                <div style="padding: 20px; background-color: #eeeeee; text-align: center; font-size: 12px; color: #666666;">
                  <p style="margin: 0;">© Fuente: weatherapi.com</p>
                </div>
              </td>
            </tr>
          </table>
        </body>
        </html>'''

    # Attach the HTML content to the email
    message.attach(MIMEText(html_content, 'html'))

    # Send the email
    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.starttls()
        server.login(smtp_username, smtp_password)
        server.sendmail(sender_email, receiver_email, message.as_string())


# Tareas
##1. Extraccion
task_1 = PythonOperator(
    task_id='extract_data',
    python_callable=extract_data,
    op_args=["{{ ds }}"],  # Use only "{{ ds }}" without hour
    dag=BC_dag,
)

# 2. Transformacion
task_2 = PythonOperator(
    task_id='transform_data',
    python_callable=transform_data,
    op_args=["{{ ds }}"],
    dag=BC_dag,
)

# 3. Conexion y carga de data
task_3 = PythonOperator(
    task_id='upload_data',
    python_callable=upload_data,
    op_args=["{{ ds }}"],
    dag=BC_dag,
)

task_4 = PythonOperator(
    task_id='send_email',
    python_callable=send_email,
    op_args=["{{ ds }}"],
    dag=BC_dag,
)


# Definicion orden de tareas
task_1 >> task_2 >> task_3 >> task_4
