import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium

st.title("RENO Dashboard")

# Try to load listings.csv
try:
    df = pd.read_csv("listings.csv")
    st.success(f"Loaded {len(df)} listings successfully!")
    
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
