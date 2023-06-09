import datetime as dt
import pandas as pd

from psycopg2.extras import execute_values
import json
import psycopg2



def load_to_redshift(conn, table_name, dataframe):
    dataframe = dataframe.reset_index(drop=True)
    
    dtypes= dataframe.dtypes
    cols= list(dtypes.index )
    tipos= list(dtypes.values)
    type_map = {'int64': 'INT','int32': 'INT','float64': 'FLOAT','object': 'VARCHAR(50)','bool':'BOOLEAN'}
    sql_dtypes = [type_map[str(dtype)] for dtype in tipos]
    # Definir formato SQL VARIABLE TIPO_DATO
    column_defs = [f"{name} {data_type}" for name, data_type in zip(cols, sql_dtypes)]
    # Combine column definitions into the CREATE TABLE statement
    table_schema = f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            {', '.join(column_defs)}
            ,PRIMARY KEY (lat,long,date)
        );
        """

    # Crear la tabla
    cur = conn.cursor()
    cur.execute(table_schema)

    # Generar los valores a insertar
    values = [tuple(x) for x in dataframe.to_numpy()]

    # Definir el INSERT
    insert_sql = f""" 
                INSERT INTO {table_name} ({', '.join(cols)}) VALUES %s
                """

    # Execute the transaction to insert the data
    cur.execute("BEGIN")
    try:
        for i, row in dataframe.iterrows():   
            cur.execute(f'''
                SELECT COUNT(*) FROM {table_name}
                WHERE "date" = %s AND lat = %s AND long = %s
            ''', (
                row['date'],
                row['lat'],
                row['long']
            ))
            count = cur.fetchone()[0]
            if count != 0:
                cur.execute(f'''
                    DELETE FROM {table_name}
                    WHERE "date" = %s AND lat = %s AND long = %s
                    ''', (
                        row['date'],
                        row['lat'],
                        row['long'])) 
            execute_values(cur, insert_sql, [values[i]])
        cur.execute("COMMIT")
    except:
        cur.execute("ROLLBACK")
        raise Exception
    #execute_values(cur, insert_sql, values)
    
    print('Proceso terminado')


def conn_redshift(path_to_creds):
    with open(path_to_creds,'r') as f:
        creds= f.read()
        creds = json.loads(creds)
    try:
        con_db_coder = psycopg2.connect(
            host=creds["host"],
            dbname=creds["data_base"],
            user=creds["user"],
            password=creds["pwd"],
            port='5439'
        )
        print("Connected to Redshift successfully!")
        return con_db_coder
        
    except Exception as e:
        print("Unable to connect to Redshift.")
        print(e)


