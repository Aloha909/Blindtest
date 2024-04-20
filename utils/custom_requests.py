import requests


def get(url, **kwargs):
    if 'timeout' not in kwargs:
        kwargs['timeout'] = 1
    while True:
        try:
            r = requests.get(url, **kwargs)
            return r
        except requests.exceptions.RequestException as e:
            print(f"An error occurred: {e}")
            kwargs['timeout'] += 1
            continue
