import re
import requests
from urllib.parse import urlparse, parse_qs
import base64
import json
try:
    from . import coordinates_scraper
except Exception:
    import coordinates_scraper
import parsel


headers = {
    'accept': '*/*',
    'accept-language': 'en-US,en;q=0.9,ur;q=0.8,ro;q=0.7,lt;q=0.6',
    'cache-control': 'no-cache',
    'content-type': 'application/json',
    'ect': '4g',
    'pragma': 'no-cache',
    'priority': 'u=1, i',
    'referer': 'https://www.airbnb.com/rooms/32781798',
    'sec-ch-device-memory': '8',
    'sec-ch-dpr': '1',
    'sec-ch-ua': '"Google Chrome";v="135", "Not-A.Brand";v="8", "Chromium";v="135"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-ch-ua-platform-version': '"19.0.0"',
    'sec-ch-viewport-width': '1365',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-origin',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36',
    'x-airbnb-api-key': 'd306zoyjsyarp7ifhu67rjxn52tv0t20',
    'x-airbnb-graphql-platform': 'web',
    'x-airbnb-graphql-platform-client': 'minimalist-niobe',
    'x-airbnb-supports-airlock-v2': 'true',
    'x-client-request-id': '0ut62m603yjs7a0q22ma6016yz4b',
    'x-client-version': '4f54190e8b9142d340c091a6f20cfb6e502134ce',
    'x-csrf-token': '',
    'x-csrf-without-token': '1',
    'x-niobe-short-circuited': 'true',
}


def main(url):

    res = requests.get(url)
    selector = parsel.Selector(res.text)
    parsed = urlparse(url)
    room_id = parsed.path.split('/')[2]
    params = parse_qs(parsed.query)
    
    # Base parameters
    api_params = {
        'operationName': 'StaysPdpSections',
        'locale': 'en',
        'currency': 'USD',
        'extensions': '{"persistedQuery":{"version":1,"sha256Hash":"6f2c582da19b486271d60c4b19e7bdd1147184662f1f4e9a83b08211a73d7343"}}'
    }

    # Build dynamic variables
    variables = {
        "id": base64.b64encode(f"StayListing:{room_id}".encode()).decode(),
        "pdpSectionsRequest": {
            "checkIn": params.get('check_in', [None])[0],
            "checkOut": params.get('check_out', [None])[0],
            "adults": params.get('adults', ['1'])[0],
            "p3ImpressionId": params.get('source_impression_id', [''])[0],
            # Keep other parameters from original request
            "amenityFilters": None,
            "bypassTargetings": False,
            "layouts": ["SIDEBAR", "SINGLE_COLUMN"],
            # ... (include other parameters from your original variables)
        }
    }
    
    api_params['variables'] = json.dumps(variables)

    response = requests.get(
        'https://www.airbnb.com/api/v3/StaysPdpSections/6f2c582da19b486271d60c4b19e7bdd1147184662f1f4e9a83b08211a73d7343',
        params=api_params,
        headers=headers
    )

    metadata = response.json().get('data', {}).get('presentation', {}).get('stayProductDetailPage', {}).get('sections', {}).get('metadata', {})
    title = selector.xpath('//h2/text()').get()
    person_capacity = metadata.get('sharingConfig', {}).get('personCapacity', '')
    average_rating = metadata.get('sharingConfig', {}).get('starRating', '')
    total_reviews = metadata.get('sharingConfig', {}).get('reviewCount', '')
    latitude = metadata.get('loggingContext', {}).get('eventDataLogging', '').get('listingLat', '')
    longitude = metadata.get('loggingContext', {}).get('eventDataLogging', '').get('listingLng', '')
    meta_description = metadata.get('seoFeatures', {}).get('metaDescription', '')
    price = re.findall(r'\$[\d,]+', str(meta_description))
    if price:
        price = price[0].replace('$', '')

    geo_data = coordinates_scraper.main(latitude, longitude)

    geo_data = {}
    if latitude and longitude:
        try:
            # Ensure coordinates_scraper returns a dict or handle exceptions
            geo_data = coordinates_scraper.main(latitude, longitude)
        except Exception as e:
            print(f"Error fetching geo data: {e}")
            geo_data = {}

    data = [{
        'Source URL': url,
        'Property URL': f'https://www.airbnb.com/rooms/{room_id}',
        'Property Name': title,
        'Person Capacity': person_capacity,
        'Average Rating': average_rating,
        'Total Reviews': total_reviews,
        'Property Latitude': latitude,
        'Property Longitude': longitude,
        'Price': price if price else '',
        **geo_data
    }]

    print(data)
    return data

# Example usage
# url = "https://www.airbnb.com/rooms/42229712?check_in=2025-10-13&check_out=2025-10-18&search_mode=regular_search&source_impression_id=p3_1744569645_P3Ndc5Rc3Ry2L9W7&previous_page_section_name=1000&federated_search_id=f9184394-7847-4204-9237-9a3deb868a74"
# response = main(url)
