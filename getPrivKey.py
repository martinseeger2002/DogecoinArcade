import configparser
from bitcoinrpc.authproxy import AuthServiceProxy

def load_rpc_config(coin_type, config_file='rpc.conf'):
    config = configparser.ConfigParser()
    config.read(config_file)

    section = f'{coin_type}_rpc'
    rpc_user = config.get(section, 'user')
    rpc_password = config.get(section, 'password')
    rpc_host = config.get(section, 'host')
    rpc_port = config.get(section, 'port')

    return rpc_user, rpc_password, rpc_host, rpc_port

def connect_to_rpc(coin_type):
    rpc_user, rpc_password, rpc_host, rpc_port = load_rpc_config(coin_type)
    rpc_url = f"http://{rpc_user}:{rpc_password}@{rpc_host}:{rpc_port}"
    return AuthServiceProxy(rpc_url)

def get_private_key(wallet_address):
    if wallet_address.startswith('D'):
        coin_type = 'dogecoin'
    elif wallet_address.startswith('be'):
        coin_type = 'bellscoin'
    else:
        return "Error: Unsupported address format"

    rpc_connection = connect_to_rpc(coin_type)
    try:
        privkey = rpc_connection.dumpprivkey(wallet_address)
        return privkey
    except Exception as e:
        return f"Error: {str(e)}"