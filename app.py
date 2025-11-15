"""
RENO v2.0 - all-in-one Streamlit dashboard
Features:
 - Map / Table / Favourites / Settings tabs
 - Manual scraper trigger (runs scraper.py or scrape_listings.py if found)
 - Last-updated timestamp for listings.csv
 - Keyword + price filters
 - Save favourites (persisted to favourites.csv)
 - Export filtered results (CSV download)
 - Display images if `image_url` column exists, else placeholder
 - Dark mode toggle (CSS)
 - Robust file/column handling
"""

import streamlit as st
import pandas as pd
import os
import subprocess
import sys
from datetime import datetime
import folium
from streamlit_folium import st_folium
import io
import base64

# -----------------------
# Configuration
# -----------------------
st.set_page_config(page_title="RENO v2.0", layout="wide")
PLACEHOLDER_IMAGE = "https://upload.wikimedia.org/wikipedia/commons/6/6b/Bitmap_VS_SVG.svg"  # simple placeholder
CSV_FILE = "listings.csv"
FAV_FILE = "favourites.csv"
SCRAPER_FILES = ["scrape_listings.py"]

# -----------------------
# Helper functions
# -----------------------
def ensure_csv_exists(path, cols=None):
    if not os.path.exists(path) or os.path.getsize(path) == 0:
        if cols:
            pd.DataFrame(columns=cols).to_csv(path, index=False)
        else:
            open(path, "w").close()

def read_listings(path):
    try:
        df = pd.read_csv(path)
        return df
    except pd.errors.EmptyDataError:
        return pd.DataFrame()
    except FileNotFoundError:
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Error reading {path}: {e}")
        return pd.DataFrame()

def normalize_columns(df):
    # rename latitude/longitude to lat/lon if needed
    colmap = {}
    if "latitude" in df.columns and "lat" not in df.columns:
        colmap["latitude"] = "lat"
    if "longitude" in df.columns and "lon" not in df.columns:
        colmap["longitude"] = "lon"
    # price variations
    if "price_raw" not in df.columns and "price" not in df.columns and "price_gbp" in df.columns:
        colmap["price_gbp"] = "price"
    if colmap:
        df = df.rename(columns=colmap)
    return df

def ensure_numeric_price(df):
    if "price" in df.columns:
        try:
            df["price"] = pd.to_numeric(df["price"], errors="coerce")
        except Exception:
            pass
    elif "price_raw" in df.columns:
        df["price"] = pd.to_numeric(df["price_raw"], errors="coerce")
    else:
        df["price"] = pd.NA
    return df

def geo_ready(df):
    return ("lat" in df.columns and "lon" in df.columns) or ("latitude" in df.columns and "longitude" in df.columns)

def show_image_from_url(url, width=200):
    # small helper; Streamlit can render images directly. We return an img tag for table use.
    if not url or not isinstance(url, str) or url.strip() == "":
        url = PLACEHOLDER_IMAGE
    return url

def run_scraper_and_log():
    # Try to run a known scraper file. Return (success_bool, output_text)
    for f in SCRAPER_FILES:
        if os.path.exists(f):
            try:
                # use same python interpreter
                proc = subprocess.run([sys.executable, f], capture_output=True, text=True, check=False)
                out = proc.stdout + "\n" + proc.stderr
                success = proc.returncode == 0
                return success, f, out
            except Exception as e:
                return False, f, str(e)
    return False, None, "No scraper file found (searching: " + ", ".join(SCRAPER_FILES) + ")"

def df_to_csv_bytes(df):
    buf = io.StringIO()
    df.to_csv(buf, index=False)
    return buf.getvalue().encode("utf-8")

def append_favourite(fav_row):
    # Load existing favourites, append if URL not duplicate
    ensure_csv_exists(FAV_FILE, cols=["title","price","address","url","description","lat","lon","image_url","source","saved_at"])
    try:
        fav_df = pd.read_csv(FAV_FILE)
    except Exception:
        fav_df = pd.DataFrame()
    url = fav_row.get("url","")
    if url and not (fav_df['url'].astype(str) == str(url)).any():
        new = {k: fav_row.get(k, "") for k in ["title","price","address","url","description","lat","lon","image_url","source"]}
        new["saved_at"] = datetime.utcnow().isoformat()
        fav_df = fav_df.append(new, ignore_index=True)
        fav_df.to_csv(FAV_FILE, index=False)
        return True
    return False

def load_favourites():
    ensure_csv_exists(FAV_FILE, cols=["title","price","address","url","description","lat","lon","image_url","source","saved_at"])
    try:
        return pd.read_csv(FAV_FILE)
    except Exception:
        return pd.DataFrame()

# -----------------------
# Ensure files exist (prevent crashes)
# -----------------------
ensure_csv_exists(CSV_FILE, cols=[
    "title","price","price_raw","type","description","address","lat","lon","image_url","source","url","distance_miles"
])
ensure_csv_exists(FAV_FILE, cols=["title","price","address","url","description","lat","lon","image_url","source","saved_at"])

# -----------------------
# UI: header + theme toggle
# -----------------------
st.title("🏡 RENO v2.0 — Renovation Opportunity Finder")
col_h1, col_h2 = st.columns([3,1])

with col_h2:
    if "dark_mode" not in st.session_state:
        st.session_state.dark_mode = False
    dm = st.checkbox("Dark mode", value=st.session_state.dark_mode)
    st.session_state.dark_mode = dm

    # Simple CSS to invert background when dark mode selected
    if dm:
        st.markdown(
            """
            <style>
            .css-1d391kg { background-color: #0e1117; }
            .stApp { background-color: #0b1020; color: #e6eef6; }
            .streamlit-expanderHeader { color: #e6eef6; }
            </style>
            """, unsafe_allow_html=True
        )

# -----------------------
# Load and prepare listings
# -----------------------
df = read_listings(CSV_FILE)
df = normalize_columns(df)
df = ensure_numeric_price(df)

# Keep a copy of original for exports
df_original = df.copy()

# Show last updated timestamp
if os.path.exists(CSV_FILE) and os.path.getsize(CSV_FILE) > 0:
    last_mod = datetime.fromtimestamp(os.path.getmtime(CSV_FILE))
    st.caption(f"Listings file: `{CSV_FILE}` • Last updated: {last_mod.strftime('%Y-%m-%d %H:%M:%S')}")
else:
    st.warning(f"No listings found in `{CSV_FILE}`. Run the scraper or upload a CSV with required columns.")
    st.stop()

# Sidebar quick controls (global)
st.sidebar.header("Quick Actions")
if st.sidebar.button("Run scraper (manual)"):
    ok, fname, out = run_scraper_and_log()
    if ok:
        st.sidebar.success(f"Scraper {fname} ran successfully.")
    else:
        if fname:
            st.sidebar.error(f"Scraper {fname} failed. See log below.")
        else:
            st.sidebar.warning(out)
    with st.expander("Scraper output / log"):
        st.text(out)

# -----------------------
# Tabs: Map / Table / Favourites / Settings
# -----------------------
tab = st.tabs(["Map", "Table", "Favourites", "Settings"])
tab_map, tab_table, tab_favs, tab_settings = tab

# -----------------------
# Shared filters (sidebar)
# -----------------------
with st.sidebar:
    st.subheader("Filters")
    max_price = st.number_input("Max price (£)", min_value=0, value=int(df["price"].fillna(0).max() if not df.empty else 600000))
    kw_input = st.text_input("Keywords (comma-separated)", value="renovation,modernisation")
    radius_miles = st.slider("Radius (miles) (informational)", 5, 100, 30)
    center_input = st.text_input("Center (town/postcode) - informational", "Stratford-upon-Avon")

# Build filter mask
filtered = df.copy()
if "price" in filtered.columns:
    filtered = filtered[filtered["price"].fillna(1e12) <= float(max_price)]

kw_list = [k.strip().lower() for k in kw_input.split(",") if k.strip()]
if kw_list:
    mask = pd.Series(False, index=filtered.index)
    for kw in kw_list:
        mask = mask | filtered.get("description", pd.Series("")).astype(str).str.lower().str.contains(kw, na=False)
        mask = mask | filtered.get("title", pd.Series("")).astype(str).str.lower().str.contains(kw, na=False)
    filtered = filtered[mask]

# Normalize lat/lon column names for map use
if "lat" not in filtered.columns and "latitude" in filtered.columns:
    filtered = filtered.rename(columns={"latitude":"lat"})
if "lon" not in filtered.columns and "longitude" in filtered.columns:
    filtered = filtered.rename(columns={"longitude":"lon"})

# Ensure image_url column exists so code doesn't crash
if "image_url" not in filtered.columns:
    filtered["image_url"] = ""

# ---------- Map tab ----------
with tab_map:
    st.header("🗺️ Map")
    if filtered.empty:
        st.info("No listings match the current filters.")
    else:
        # compute center for map
        if filtered["lat"].notna().any() and filtered["lon"].notna().any():
            center_lat = float(filtered["lat"].dropna().mean())
            center_lon = float(filtered["lon"].dropna().mean())
        else:
            center_lat, center_lon = 52.1917, -1.7073  # Stratford default

        m = folium.Map(location=[center_lat, center_lon], zoom_start=11)
        for idx, row in filtered.iterrows():
            try:
                lat = float(row["lat"])
                lon = float(row["lon"])
            except Exception:
                continue
            img = row.get("image_url", "") or PLACEHOLDER_IMAGE
            popup_html = f"<b>{row.get('title','')}</b><br>£{int(row.get('price',0)):,}<br>{row.get('address','')}"
            # include small image if exists
            if img:
                popup_html += f"<br><img src='{img}' style='max-width:200px;max-height:150px;'/>"
            folium.Marker(location=[lat, lon], popup=popup_html, tooltip=row.get("title","")).add_to(m)

        st_folium(m, width="100%", height=650)

# ---------- Table tab ----------
with tab_table:
    st.header("📋 Listings Table")
    if filtered.empty:
        st.info("No listings to show.")
    else:
        # Show images as URLs (clickable) and a small preview in expander details
        # Table display
        display_cols = ["title","price","address","description","source","url","image_url"]
        existing_cols = [c for c in display_cols if c in filtered.columns]
        st.dataframe(filtered[existing_cols].fillna(""), use_container_width=True, height=350)

        # Download filtered CSV
        csv_bytes = df_to_csv_bytes(filtered)
        st.download_button("Download filtered results (CSV)", data=csv_bytes, file_name="reno_filtered.csv", mime="text/csv")

        st.markdown("---")
        st.subheader("Listing preview & actions")
        # Choose a listing to inspect and favourite
        idx = st.selectbox("Pick a listing", options=filtered.index.tolist(), format_func=lambda i: filtered.loc[i,"title"])
        item = filtered.loc[idx]

        cols = st.columns([2,1])
        with cols[0]:
            st.write(f"### {item.get('title','')}")
            st.write(f"**Price:** £{int(item.get('price',0)):,}")
            st.write(f"**Address:** {item.get('address','')}")
            st.write("**Description:**")
            st.write(item.get("description",""))
            st.write("**Source:**", item.get("source",""))
            if item.get("url"):
                st.markdown(f"[Open listing]({item.get('url')})")
            # Favourite button
            if st.button("⭐ Save to favourites"):
                ok = append_favourite(item.to_dict())
                if ok:
                    st.success("Saved to favourites")
                else:
                    st.info("Already in favourites")

        with cols[1]:
            img_url = item.get("image_url") if item.get("image_url") else PLACEHOLDER_IMAGE
            try:
                st.image(img_url, width=300)
            except Exception:
                st.image(PLACEHOLDER_IMAGE, width=300)

# ---------- Favourites tab ----------
with tab_favs:
    st.header("⭐ Favourites")
    fav_df = load_favourites()
    if fav_df.empty:
        st.info("No favourites saved yet.")
    else:
        st.dataframe(fav_df.fillna(""), use_container_width=True, height=300)
        fav_csv = df_to_csv_bytes(fav_df)
        st.download_button("Download favourites (CSV)", data=fav_csv, file_name="reno_favourites.csv", mime="text/csv")
        if st.button("Clear all favourites"):
            # clear file
            pd.DataFrame(columns=fav_df.columns).to_csv(FAV_FILE, index=False)
            st.success("Cleared favourites")
            st.experimental_rerun()

# ---------- Settings tab ----------
with tab_settings:
    st.header("⚙️ Settings")
    st.write("Project configuration and notes.")
    st.markdown(
        """
        - Manual scraper: click **Run scraper (manual)** in the sidebar to run the local scraper script (scraper.py or scrape_listings.py).
        - The app expects `listings.csv` to exist in the same directory as `app.py`.
        - `image_url` column is optional — placeholder images are used when missing.
        - Favourites are saved in `favourites.csv`.
        """
    )
    if st.button("Open data folder (info)"):
        st.info(f"App working directory: `{os.getcwd()}`\nFiles present: {os.listdir('.')[:50]}")

# End
