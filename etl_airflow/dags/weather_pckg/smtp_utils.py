import json
def get_login(path_to_creds):
    with open(path_to_creds, 'r') as f:
        creds = f.read()
        creds = json.loads(creds)

    smtp_port = creds["smtp_port"]
    smtp_server = creds["smtp_server"]
    smtp_username = creds["smtp_username"]
    smtp_password = creds["smtp_password"]

    return smtp_port, smtp_server, smtp_username, smtp_password

