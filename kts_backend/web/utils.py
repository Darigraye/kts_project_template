def build_query(host: str, method: str, params: dict) -> str:
    url = 'https://' + host + method + '?'
    if 'v' not in params:
        params['v'] = '5.131'
    url += '&'.join([f'{key}={value}' for key, value in params.items()])
    return url
