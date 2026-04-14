import httpx
import re
import json
from datetime import datetime, timezone


def parse_price(price_str):
    if not price_str:
        return {'eur': None, 'local': None}
    
    parts = price_str.strip().split()
    if len(parts) >= 2 and parts[0] == '€':
        eur_price = parts[1]
        local_price = ' '.join(parts[2:]) if len(parts) > 2 else None
        return {'eur': eur_price, 'local': local_price}
    
    return {'eur': None, 'local': price_str}


def parse_data_date(html):
    date_match = re.search(r'as of (\d+)\. (\w+) (\d{4})', html)
    if date_match:
        day, month_name, year = date_match.groups()
        month_map = {
            'January': '01', 'February': '02', 'March': '03', 'April': '04',
            'May': '05', 'June': '06', 'July': '07', 'August': '08',
            'September': '09', 'October': '10', 'November': '11', 'December': '12'
        }
        return f"{year}-{month_map.get(month_name, '01')}-{int(day):02d}"
    return None


def get_fuel_prices():
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    }

    response = httpx.get('https://www.tolls.eu/fuel-prices', headers=headers, timeout=30)
    response.raise_for_status()

    html = response.text
    data_date = parse_data_date(html)
    rows = re.findall(r'<div class="tr[^"]*"[^>]*>(.*?)</div>\s*</div>', html, re.DOTALL)

    countries = {}
    for row in rows[1:]:
        cells = re.findall(r'<div class="td[^"]*"[^>]*>(.*?)</div>', row, re.DOTALL)
        if len(cells) >= 3:
            country = re.sub(r'<[^>]+>', '', cells[1]).strip()
            if country:
                countries[country] = {
                    'gasoline95': parse_price(re.sub(r'<[^>]+>', '', cells[2]).strip() if len(cells) > 2 else ''),
                    'diesel': parse_price(re.sub(r'<[^>]+>', '', cells[3]).strip() if len(cells) > 3 else ''),
                    'lpg': parse_price(re.sub(r'<[^>]+>', '', cells[4]).strip() if len(cells) > 4 else '')
                }

    return {
        'continent': 'europe',
        'data_date': data_date,
        'updated_at': datetime.now(timezone.utc).isoformat(),
        'countries': countries
    }


if __name__ == "__main__":
    data = get_fuel_prices()
    print(json.dumps(data, indent=2, ensure_ascii=False))
