import httpx
import re
import json
from datetime import datetime, timezone


def get_gasoline_prices(continent='world'):
    base_url = "https://tradingeconomics.com/country-list/gasoline-prices"
    url = f"{base_url}?continent={continent}" if continent != 'europe' else base_url
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    }
    
    response = httpx.get(url, headers=headers, timeout=30)
    response.raise_for_status()
    
    html = response.text
    
    tables = re.findall(r'<table[^>]*>(.*?)</table>', html, re.DOTALL)
    if not tables:
        raise ValueError("No table found on page")
    
    rows = re.findall(r'<tr[^>]*>(.*?)</tr>', tables[0], re.DOTALL)
    
    countries = []
    for row in rows:
        cells = re.findall(r'<td[^>]*>(.*?)</td>', row, re.DOTALL)
        if len(cells) >= 5:
            try:
                country = {
                    "country": re.sub(r'<[^>]+>', '', cells[0]).strip(),
                    "last": float(re.sub(r'<[^>]+>', '', cells[1]).strip()),
                    "previous": float(re.sub(r'<[^>]+>', '', cells[2]).strip()),
                    "reference": re.sub(r'<[^>]+>', '', cells[3]).strip(),
                    "unit": re.sub(r'<[^>]+>', '', cells[4]).strip(),
                }
                countries.append(country)
            except (ValueError, IndexError):
                pass
    
    return {
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "continent": continent,
        "countries": countries
    }


if __name__ == "__main__":
    data = get_gasoline_prices()
    print(json.dumps(data, indent=2, ensure_ascii=False))
