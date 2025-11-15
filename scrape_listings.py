import time
import json
from datetime import datetime

def run_scraper():
    """
    TEST SCRAPER — does not scrape any websites.
    Generates fake listings and writes them to listings.csv.
    """

    print("Starting test scraper...")
    time.sleep(1)

    # Generate sample listings with placeholder images
    sample_data = [
        {
            "title": "Test House 1",
            "price": 250000,
            "address": "123 Sample Road, Stratford-upon-Avon",
            "latitude": 52.19173,
            "longitude": -1.70742,
            "image_url": "https://via.placeholder.com/300x200.png?text=House+1"
        },
        {
            "title": "Test House 2",
            "price": 350000,
            "address": "45 Demo Street, Stratford-upon-Avon",
            "latitude": 52.19210,
            "longitude": -1.70800,
            "image_url": "https://via.placeholder.com/300x200.png?text=House+2"
        }
    ]

    # Save to CSV
    import pandas as pd
    df = pd.DataFrame(sample_data)
    df.to_csv("listings.csv", index=False)

    # Write a log file
    with open("scraper_log.txt", "a") as log:
        log.write(f"[{datetime.now()}] Test scraper ran successfully.\n")

    print("Scraper finished — listings.csv updated.")
    print("Generated 2 fake sample listings.")
    return True


if __name__ == "__main__":
    run_scraper()
