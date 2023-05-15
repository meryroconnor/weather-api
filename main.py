import pandas as pd
from datetime import datetime


def request_data(date=today):
    key=get_api_key(".env/api_key.txt")
    base_url = "http://api.weatherapi.com/v1/history.json"
    url = f"{base_url}?key={key}&q=Buenos Aires&dt={today}"
    response = requests.get(url)
    data = response.json()
    df = pd.DataFrame({"fecha":today,"temp_min":data["forecast"]["temp_min"]
                ,"temp_max":data["forecast"]["temp_max"],})
    
    return df


if __name__ == "__main__":
    today = datetime.today().strftime('%Y-%m-%d')
    data = request_data(date=today)
    conn_db_coder = conn_redshift(".env/pwd_coder.txt")
    cargar_en_redshift(conn=conn_db_coder, table_name="books",dataframe=data)