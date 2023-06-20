import requests
import pandas as pd

import json


def get_api_key(path):
    with open(path,'r') as f:
        key_api= f.read()
        key_api = json.loads(key_api)
    return key_api["pwd"]

def request_forecast(date):
    try:
        key=get_api_key(".creds/api_key.txt")
        base_url = "http://api.weatherapi.com/v1/history.json"
        url = f"{base_url}?key={key}&q=Buenos Aires&dt={date}"
        response = requests.get(url)
        data = response.json()
        latitud= data["location"]["lat"]
        longitud= data["location"]["lon"]
        city = "Buenos Aires"
        country = "Argentina"
        mintemp_c= data["forecast"]["forecastday"][0]["day"]["mintemp_c"]
        maxtemp_c= data["forecast"]["forecastday"][0]["day"]["maxtemp_c"]
        avgtemp_c = data["forecast"]["forecastday"][0]["day"]["avgtemp_c"]
        avghumidity= data["forecast"]["forecastday"][0]["day"]["avghumidity"]
        totalprecip_mm= data["forecast"]["forecastday"][0]["day"]["totalprecip_mm"]
        description=data["forecast"]["forecastday"][0]["day"]["condition"]["text"]

        df = pd.DataFrame([{"date":date,"lat":latitud,"long":longitud,"country":country, "city":city
                            ,"mintemp_c":mintemp_c,"maxtemp_c":maxtemp_c, "avgtemp_c":avgtemp_c
                            ,"avghumidity":avghumidity,"totalprecip_mm":totalprecip_mm,"description":description}])
        return df
    except Exception as e:
        print(e)



import yaml

def load_yaml(path="config.yaml"):
      with open(path, "r") as stream:
            try:
                  return yaml.safe_load(stream)
            except yaml.YAMLError as exc:
                  return exc

def init_settings():
    config = load_yaml()
    start_date = config["start_date"]
    end_date = config["end_date"]
    return start_date, end_date