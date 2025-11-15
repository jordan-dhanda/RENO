import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import os
from datetime import datetime

st.set_page_config(page_title="RENO", layout="wide")
st.title("🏡 RENO Property Dashboard")

CSV_FILE = "listings.csv"

# -----------------------
# Load CSV safely
# -----------------------
if not os.path.exists(CSV_FILE):
    st.warning("No listings.csv file found. Please upload it.")
    st.stop()

try:
    df = pd.read_csv(CSV_FILE)
except Exception as e:
    st.error(f"Error loading CSV: {e}")
    st.stop()

# Validate required columns
required_cols = ["title", "price", "description", "address", "lat", "lon"]
missing = [c for c in required_cols if c not in df.columns]

if missing:
    st.error(f"Missing required columns: {missing}")
    st.stop()

st.success(f"Loaded {len(df)} listings")

# Timestamp
timestamp = datetime.fromtimestamp(os.path.getmtime(CSV_FILE))
st.caption(f"Last updated: **{timestamp.strftime('%Y-%m-%d %H:%M:%S')}**")

# ---------------------------------
# Sidebar Filters
# ---------------------------------
st.sidebar.header("Filters")

max_price = st.sidebar.number_input("Max Price (£)", value=600000, step=50000)
keywords = st.sidebar.text_input("Keywords", value="renovation,modernisation")

kw_list = [k.strip().lower() for k in keywords.split(",") if k.strip()]

# Filter logic
filtered_df = df[df["price"] <= max_price]

if kw_list:
    filtered_df = filtered_df[
        df["description"].str.lower().str.contains("|".join(kw_list)) |
        df["title"].str.lower().str.contains("|".join(kw_list))
    ]

st.subheader(f"📋 Filtered Listings ({len(filtered_df)})")
st.dataframe(filtered_df, height=300)

# ---------------------------------
# Detail view when clicking a row
# ---------------------------------
st.subheader("🔍 Listing Details")

selected_index = st.selectbox(
    "Choose a listing to inspect:",
    options=filtered_df.index,
    format_func=lambda i: filtered_df.loc[i, "title"]
)

item = filtered_df.loc[selected_index]

st.write(f"### {item['title']}")
st.write(f"**Price:** £{item['price']:,}")
st.write(f"**Address:** {item['address']}")
st.write("**Description:**")
st.write(item["description"])

# ---------------------------------
# Map View
# ---------------------------------
st.subheader("🗺️ Map View")

m = folium.Map(
    location=[filtered_df["lat"].mean(), filtered_df["lon"].mean()],
    zoom_start=11
)

for _, row in filtered_df.iterrows():
    popup = (
        f"<b>{row['title']}</b><br>"
        f"£{row['price']:,}<br>"
        f"{row['address']}"
    )

    folium.Marker(
        location=[row["lat"], row["lon"]],
        popup=popup,
        tooltip=row["title"]
    ).add_to(m)

st_folium(m, height=500, width=900)
