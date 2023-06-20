from datetime import timedelta, datetime
from weather_pckg.api_utils import request_forecast
from weather_pckg.redshift_utils import load_to_redshift,conn_redshift
from weather_pckg.transform import calculate_humidity_ratio,calculate_mean_avg_humidity

import pandas as pd
import numpy as np
import os

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
    schedule_interval="@daily",
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


# Definicion orden de tareas
task_1 >> task_2 >> task_3