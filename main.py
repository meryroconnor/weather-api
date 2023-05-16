
from datetime import datetime
from redshift_utils import request_data,conn_redshift,load_to_redshift

if __name__ == "__main__":
    today = datetime.today()
    data = request_data(date=today)
    conn_db_coder = conn_redshift(".env/pwd_coder.txt")
    load_to_redshift(conn=conn_db_coder, table_name="forecast",dataframe=data)