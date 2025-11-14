import requests
from bs4 import BeautifulSoup
import pandas as pd
from geopy.geocoders import Nominatim
import time

# -------------------------------
# CONFIG
# -------------------------------
LOCATION = "Stratford-upon-Avon, UK"
RADIUS_MILES = 30
MAX_PRICE = 600000
KEYWORDS = ["renovation", "modernisation"]
PROPERTY_TYPES = ["houses", "land"]

OUTPUT_FILE = "listings.csv"

geolocator = Nominatim(user_agent="reno_app")

# -------------------------------
# Helper functions
# -------------------------------
def geocode_address(address):
    try:
        location = geolocator.geocode(address)
        if location:
            return location.latitude, location.longitude
    except:
        return None, None
    return None, None

def scrape_rightmove():
    listings = []
    url = "https://www.rightmove.co.uk/property-for-sale/find.html"
    # Add query params for location, max price, keywords, radius
    params = {
        "locationIdentifier": "OUTCODE^1761",  # Example: Stratford-upon-Avon postcode area
        "maxPrice": MAX_PRICE,
        "keywords": " OR ".join(KEYWORDS),
        "radius": RADIUS_MILES,
        "propertyTypes": "houses",
        "includeSSTC": "false",
        "index": 0
    }
    
    response = requests.get(url, params=params)
    soup = BeautifulSoup(response.text, "html.parser")
    
    # Example: parsing Rightmove results (will vary depending on page structure)
    for card in soup.find_all("div", class_="propertyCard"):
        title_tag = card.find("h2")
        title = title_tag.get_text(strip=True) if title_tag else ""
        
        price_tag = card.find("div", class_="propertyCard-priceValue")
        price_text = price_tag.get_text(strip=True) if price_tag else ""
        price = int(price_text.replace("£","").replace(",","")) if price_text else 0
        
        address_tag = card.find("address")
        address = address_tag.get_text(strip=True) if address_tag else ""
        
        url_tag = card.find("a", href=True)
        link = "https://www.rightmove.co.uk" + url_tag['href'] if url_tag else ""
        
        description_tag = card.find("span", class_="propertyCard-title")
        description = description_tag.get_text(strip=True) if description_tag else ""
        
        lat, lon = geocode_address(address)
        
        listings.append({
            "title": title,
            "price": price,
            "address": address,
            "url": link,
            "description": description,
            "lat": lat,
            "lon": lon,
            "source": "Rightmove"
        })
        time.sleep(0.5)  # polite delay
    return listings

def scrape_zoopla():
    listings = []
    url = "https://www.zoopla.co.uk/for-sale/property/stratford-upon-avon/"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    
    for card in soup.find_all("div", class_="css-1itfubx-ListingsContainer"):
        # Example parsing — may need adjustment
        title = card.find("h2").get_text(strip=True) if card.find("h2") else ""
        price_tag = card.find("p", class_="css-wpn2c1-Text")
        price_text = price_tag.get_text(strip=True) if price_tag else ""
        price = int(price_text.replace("£","").replace(",","")) if price_text else 0
        address = card.find("p", class_="css-1n7hynb-Text").get_text(strip=True) if card.find("p", class_="css-1n7hynb-Text") else ""
        link_tag = card.find("a", href=True)
        link = "https://www.zoopla.co.uk" + link_tag['href'] if link_tag else ""
        lat, lon = geocode_address(address)
        
        listings.append({
            "title": title,
            "price": price,
            "address": address,
            "url": link,
            "description": "",
            "lat": lat,
            "lon": lon,
            "source": "Zoopla"
        })
        time.sleep(0.5)
    return listings

def scrape_onthemarket():
    listings = []
    url = "https://www.onthemarket.com/for-sale/property/stratford-upon-avon/"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    
    for card in soup.find_all("li", class_="listing"):
        title_tag = card.find("h2")
        title = title_tag.get_text(strip=True) if title_tag else ""
        price_tag = card.find("span", class_="listingPrice")
        price_text = price_tag.get_text(strip=True) if price_tag else ""
        price = int(price_text.replace("£","").replace(",","")) if price_text else 0
        address_tag = card.find("span", class_="listingAddress")
        address = address_tag.get_text(strip=True) if address_tag else ""
        link_tag = card.find("a", href=True)
        link = "https://www.onthemarket.com" + link_tag['href'] if link_tag else ""
        lat, lon = geocode_address(address)
        
        listings.append({
            "title": title,
            "price": price,
            "address": address,
            "url": link,
            "description": "",
            "lat": lat,
            "lon": lon,
            "source": "OnTheMarket"
        })
        time.sleep(0.5)
    return listings

# -------------------------------
# RUN SCRAPING
# -------------------------------
all_listings = []
all_listings.extend(scrape_rightmove())
all_listings.extend(scrape_zoopla())
all_listings.extend(scrape_onthemarket())

# -------------------------------
# SAVE TO CSV
# -------------------------------
df = pd.DataFrame(all_listings)
df.to_csv(OUTPUT_FILE, index=False)
print(f"Saved {len(df)} listings to {OUTPUT_FILE}")
