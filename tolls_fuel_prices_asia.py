import httpx
import json
from datetime import datetime, timezone
from bs4 import BeautifulSoup


def parse_price_td(td):
    if not td:
        return {'eur': None, 'local': None}

    text = td.contents[0].strip() if td.contents else ''
    span = td.find('span', class_='fuel-price-small')
    local_text = span.get_text(strip=True) if span else ''

    eur = None
    local = None

    if text.startswith('€'):
        eur = text.split()[1] if len(text.split()) > 1 else None

    if local_text:
        local_parts = local_text.split()
        if len(local_parts) >= 2:
            local = {'currency': local_parts[0], 'value': ' '.join(local_parts[1:])}
        elif len(local_parts) == 1:
            local = {'currency': local_parts[0], 'value': None}
    elif td.get_text(strip=True) == '-':
        return {'eur': None, 'local': None}

    return {'eur': eur, 'local': local}


def parse_data_date(html):
    soup = BeautifulSoup(html, 'html.parser')
    text = soup.get_text()
    import re
    date_match = re.search(r'as of (\d+)\. (\w+) (\d{4})', text)
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

    response = httpx.get('https://www.tolls.eu/fuel-prices-asia', headers=headers, timeout=30)
    response.raise_for_status()

    html = response.text
    data_date = parse_data_date(html)

    soup = BeautifulSoup(html, 'html.parser')
    rows = soup.find_all('div', class_='tr')

    countries = {}
    for row in rows:
        cells = row.find_all('div', class_='td')
        if len(cells) >= 5:
            country = cells[1].get_text(strip=True)
            if country and country != 'Country':
                countries[country] = {
                    'gasoline95': parse_price_td(cells[2]),
                    'diesel': parse_price_td(cells[3]),
                    'lpg': parse_price_td(cells[4])
                }

    return {
        'continent': 'asia',
        'data_date': data_date,
        'updated_at': datetime.now(timezone.utc).isoformat(),
        'countries': countries
    }


if __name__ == "__main__":
    data = get_fuel_prices()
    print(json.dumps(data, indent=2, ensure_ascii=False))
