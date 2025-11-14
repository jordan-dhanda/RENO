import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import os
from datetime import datetime

st.title("RENO Dashboard")

CSV_FILE = "listings.csv"

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
    
    # Display table
    st.subheader("Listings Table")
    st.dataframe(df)
    
    # Display map
    st.subheader("Map View")
    if "lat" in df.columns and "lon" in df.columns:
        m = folium.Map(location=[df["lat"].mean(), df["lon"].mean()], zoom_start=10)
        for _, row in df.iterrows():
            folium.Marker(
                location=[row["lat"], row["lon"]],
                popup=f"{row['title']} (£{row['price']})"
            ).add_to(m)
        st_folium(m, width=700)
    else:
        st.warning("Latitude and longitude columns missing from CSV.")

except FileNotFoundError:
    st.warning("listings.csv not found. Please upload it to this folder.")
