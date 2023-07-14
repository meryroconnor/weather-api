# Weather API

Consiste en llamadas a **http://api.weatherapi.com** para traer pronósticos climáticos en la provincia de Buenos aires dado un rango de días.

**files**:
* etl_airflow/dags: contiene el archivo dag_weather.py el cual contiene 4 tareas que se ejecutan todos los dias a las 6:00:
  * Extracción
  * Transformación
  * Carga en Redshift
  * Envio de Informe climático para el dia de ejecución.

![img.png](img.png)