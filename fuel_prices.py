import httpx
import json
from datetime import datetime, timezone


def get_fuel_prices():
    url = "https://lardi-trans.com/landing-web-api/fuel"
    response = httpx.get(url, follow_redirects=True, timeout=30)
    response.raise_for_status()
    data = response.json()

    result = {
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "revision": data.get("revision"),
        "week": data.get("week"),
        "year": data.get("year"),
        "countryCount": data.get("countryCount"),
        "countries": []
    }

    fuel_names = {
        "fuel_95": "A95",
        "fuel_98": "A98",
        "fuel_diesel": "Diesel",
        "fuel_lpg": "LPG"
    }

    for country in data.get("countryList", []):
        country_data = {
            "country": country["name"],
            "currency": country["currency"],
            "fuels": {}
        }

        for fuel in country.get("fuel", []):
            fuel_code = fuel["name"]
            country_data["fuels"][fuel_names.get(fuel_code, fuel_code)] = {
                "currentPrice": fuel.get("currentPrice"),
                "previousPrice": fuel.get("previousPrice")
            }

        result["countries"].append(country_data)

    return result


if __name__ == "__main__":
    data = get_fuel_prices()
    print(json.dumps(data, indent=2, ensure_ascii=False))
