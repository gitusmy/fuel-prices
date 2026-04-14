import httpx
import json
from datetime import datetime, timezone


SOURCES = [
    {'name': 'fxapi', 'url': 'https://fxapi.app/api/eur.json', 'base': 'EUR'},
    {'name': 'moneyconvert', 'url': 'https://cdn.moneyconvert.net/api/latest.json', 'base': 'EUR'},
    {'name': 'frankfurter_v2', 'url': 'https://api.frankfurter.dev/v2/rates', 'base': 'EUR'},
    {'name': 'frankfurter_v1', 'url': 'https://api.frankfurter.dev/v1/latest', 'base': 'EUR'},
]


def fetch_frankfurter_v1(url):
    response = httpx.get(url, params={'base': 'EUR'}, timeout=10)
    response.raise_for_status()
    data = response.json()
    
    rates = {}
    for code, rate in data.get('rates', {}).items():
        rates[code] = round(rate, 4)
    rates['EUR'] = 1.0
    return {
        'source': 'frankfurter',
        'base': 'EUR',
        'date': data.get('date'),
        'rates': rates
    }


def fetch_frankfurter_v2(url):
    response = httpx.get(url, params={'base': 'EUR'}, timeout=10)
    response.raise_for_status()
    data = response.json()
    
    rates = {}
    date = None
    
    # frankfurter_v2 returns a list of objects: [{'date': ..., 'base': ..., 'quote': ..., 'rate': ...}]
    if isinstance(data, list):
        for item in data:
            if date is None and item.get('date'):
                date = item.get('date')
            if item.get('quote') and item.get('rate'):
                rates[item['quote']] = round(item['rate'], 4)
    elif isinstance(data, dict) and 'rates' in data:
        for code, rate in data['rates'].items():
            rates[code] = round(rate, 4)
        date = data.get('date')
    
    rates['EUR'] = 1.0
    return {
        'source': 'frankfurter',
        'base': 'EUR',
        'date': date,
        'rates': rates
    }


def fetch_moneyconvert(url):
    response = httpx.get(url, timeout=10)
    response.raise_for_status()
    data = response.json()
    
    rates = {}
    rates_data = data.get('rates', data)
    base = data.get('base', 'USD')
    
    # Convert all rates to EUR base
    eur_rate = rates_data.get('EUR', 1.0) if base == 'USD' else 1.0
    
    for code, rate in rates_data.items():
        if isinstance(rate, (int, float)):
            # Convert from USD base to EUR base
            if base == 'USD':
                converted = rate / eur_rate if eur_rate else rate
            else:
                converted = rate
            rates[code] = round(converted, 4)
    
    rates['EUR'] = 1.0
    return {
        'source': 'moneyconvert',
        'base': 'EUR',
        'date': data.get('date'),
        'rates': rates
    }


def fetch_fxapi(url):
    response = httpx.get(url, timeout=10)
    response.raise_for_status()
    data = response.json()
    
    rates = {}
    rates_data = data if isinstance(data, dict) else {}
    
    for code, rate in rates_data.items():
        if isinstance(rate, (int, float)):
            rates[code] = round(rate, 4)
    
    if 'EUR' not in rates:
        rates['EUR'] = 1.0
    
    return {
        'source': 'fxapi',
        'base': 'EUR',
        'date': None,
        'rates': rates
    }


def get_currency_rates():
    fetchers = {
        'frankfurter_v1': fetch_frankfurter_v1,
        'frankfurter_v2': fetch_frankfurter_v2,
        'moneyconvert': fetch_moneyconvert,
        'fxapi': fetch_fxapi,
    }
    
    last_error = None
    
    for source in SOURCES:
        try:
            fetcher = fetchers.get(source['name'])
            if fetcher:
                result = fetcher(source['url'])
                if result and len(result['rates']) > 10:
                    return {
                        'source_used': source['name'],
                        'base': result['base'],
                        'date': result['date'],
                        'updated_at': datetime.now(timezone.utc).isoformat(),
                        'rates': result['rates']
                    }
        except Exception as e:
            last_error = str(e)
            continue
    
    raise Exception(f"All sources failed. Last error: {last_error}")


if __name__ == "__main__":
    data = get_currency_rates()
    print(json.dumps(data, indent=2, ensure_ascii=False))
