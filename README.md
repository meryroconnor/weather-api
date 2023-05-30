# Weather API

Consiste en llamadas a **http://api.weatherapi.com** para traer pronósticos climáticos en la provincia de Buenos aires dado un rango de días.

**files**:
* 01_extract.ipynb: notebook para llamar a la api y generar un archivo  raw csv con los datos obtenidos.
* 02_transform.ipynb: notebook para realizar procesos de etl y guardar el dataframe resultante en un csv.
* 03_load.ipynb : notebook para popular la base de datos dado un rango de fechas. Si los registros ya existen en la tabla destino, serán reemplazados por la nueva ingesta de datos.
