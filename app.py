import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import os
from datetime import datetime
import subprocess

st.set_page_config(page_title="RENO Dashboard", layout="wide")
st.title("RENO Dashboard")

CSV_FILE = "listings.csv"

# -------------------------------
# Function to run scraper manually
# -------------------------------
def run_scraper():
    try:
        subprocess.run(["python3", "scrape_listings.py"], check=True)
        st.success("Scraper ran successfully! CSV updated.")
    except Exception as e:
        st.error(f"Error running scraper: {e}")

# -------------------------------
# Refresh CSV button
# -------------------------------
if st.sidebar.button("Refresh CSV"):
    run_scraper()

# -------------------------------
# Try to load listings.csv
# -------------------------------
try:
    df = pd.read_csv(CSV_FILE)
    st.success(f"Loaded {len(df)} listings successfully!")
    
    # Show last modified timestamp
    last_modified = os.path.getmtime(CSV_FILE)
    last_modified_dt = datetime.fromtimestamp(last_modified)
    st.info(f"Listings last updated: {last_modified_dt.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # -------------------------------
    # Sidebar filters
    # -------------------------------
    st.sidebar.subheader("Filters")
    max_price = st.sidebar.number_input("Max Price (£)", value=600000, step=50000)
    keyword_filter = st.sidebar.text_input("Keywords (comma-separated)", value="renovation,modernisation")
    
    filtered_df = df[df["price"] <= max_price]
    keywords = [k.strip().lower() for k in keyword_filter.split(",")]
    if keywords:
        filtered_df = filtered_df[filtered_df["title"].str.lower().str.contains("|".join(keywords)) | 
                                  filtered_df["description"].str.lower().str.contains("|".join(keywords))]

    st.subheader(f"Listings Table ({len(filtered_df)})")
    st.dataframe(filtered_df)
    
    # -------------------------------
    # Map view
    # -------------------------------
    st.subheader("Map View")
    if "lat" in filtered_df.columns and "lon" in filtered_df.columns:
        m = folium.Map(location=[filtered_df["lat"].mean(), filtered_df["lon"].mean()], zoom_start=10)
        for _, row in filtered_df.iterrows():
            folium.Marker(
                location=[row["lat"], row["lon"]],
                popup=f"{row['title']} (£{row['price']})\n{row['address']}",
                tooltip=row['title']
            ).add_to(m)
        st_folium(m, width=700)
    else:
        st.warning("Latitude and longitude columns missing from CSV.")

except FileNotFoundError:
    st.warning("listings.csv not found. Please upload it or run the scraper.")
