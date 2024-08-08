import configparser
from bitcoinrpc.authproxy import AuthServiceProxy

def load_rpc_config(config_file='rpc.conf'):
    config = configparser.ConfigParser()
    config.read(config_file)

    rpc_user = config.get('rpc', 'user')
    rpc_password = config.get('rpc', 'password')
    rpc_host = config.get('rpc', 'host')
    rpc_port = config.get('rpc', 'port')

    return rpc_user, rpc_password, rpc_host, rpc_port

def connect_to_rpc():
    rpc_user, rpc_password, rpc_host, rpc_port = load_rpc_config()
    rpc_url = f"http://{rpc_user}:{rpc_password}@{rpc_host}:{rpc_port}"
    return AuthServiceProxy(rpc_url)

def get_private_key(wallet_address):
    rpc_connection = connect_to_rpc()
    try:
        privkey = rpc_connection.dumpprivkey(wallet_address)
        return privkey
    except Exception as e:
        return f"Error: {str(e)}"
