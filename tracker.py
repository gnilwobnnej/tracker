import streamlit as st
import pandas as pd
import geopandas as gpd
import folium
from folium.plugins import MarkerCluster, HeatMap
from streamlit_folium import st_folium
import requests

st.set_page_config(page_title="Species Sightings Map", layout="wide")
st.title("Species Sightings Map (GBIF)")

# Common species dictionary
common_species = {
    "Bald Eagle": "Haliaeetus leucocephalus",
    "American Black Bear": "Ursus americanus",
    "White-tailed Deer": "Odocoileus virginianus",
    "American Alligator": "Alligator mississippiensis",
    "Eastern Bluebird": "Sialia sialis",
    "Great Tit": "Parus major major"
}

# Multi-select box for species
selected_species = st.multiselect(
    "Select species to map:",
    options=list(common_species.keys()),
    default=["Bald Eagle"]
)

# text input for scientific name
user_scientific_name = st.text_input("Or enter a scientific name(e.g. Panthera leo): ").strip()

# toggle for heatmap
show_heatmap = st.checkbox("Show Heatmap", value = False)


def fetch_species_data(scientific_name, limit = 500):
    """Fetch GBIF data for a given species"""
    url = "https://api.gbif.org/v1/occurrence/search"
    params = {
        "scientificName": scientific_name,
        "limit": limit,
        "hasCoordinate": True
    }
    try:
        r = requests.get(url, params=params, timeout=15)
        results = r.json().get("results", [])
        df = pd.json_normalize(results)
        df = df[['scientificName', 'decimalLatitude', 'decimalLongitude', 'eventDate']]
        df = df.dropna(subset=["decimalLatitude", "decimalLongitude"])
        df['color'] = scientific_name  # placeholder for grouping
        return df
    except Exception as e:
        st.error(f"Error fetching data for {scientific_name}: {e}")
        return pd.DataFrame()

# fetch and diplay data
if selected_species or user_scientific_name:
    with st.spinner("Fetching sightings..."):
        all_sightings = []

        # fetch from drop down
        for name in selected_species:
            sci = common_species[name]
            df = fetch_species_data(sci)
            df["commonName"] = name
            all_sightings.append(df)

        #fetch from text input
        if user_scientific_name:
            sci = user_scientific_name
            df = fetch_species_data(sci)
            if not df.empty:
                df["commonName"] = sci
                all_sightings.append(df)



        if all_sightings:
            combined_df = pd.concat(all_sightings, ignore_index=True)
            gdf = gpd.GeoDataFrame(combined_df, geometry=gpd.points_from_xy(
                combined_df["decimalLongitude"], combined_df["decimalLatitude"]
            ))

            
            #computes bounds of all sightings. 
            minx, miny, maxx, maxy = gdf.total_bounds
            center_lat = (miny + maxy) / 2
            center_lon = (minx + maxx) / 2

            # initialize map based on sightings
            m = folium.Map(location=[center_lat, center_lon], zoom_start=4)
            colors = ["red", "blue", "green", "purple", "orange", "darkred", "cadetblue"]

            for i, (species_name, group) in enumerate(gdf.groupby("commonName")):
                color = colors[i % len(colors)]
                cluster = MarkerCluster(name=species_name).add_to(m)
                for _, row in group.iterrows():
                    folium.Marker(
                        location=[row.geometry.y, row.geometry.x],
                        popup=f"<b>{row['commonName']}</b><br>{row['eventDate']}",
                        icon=folium.Icon(color=color, icon="leaf")
                    ).add_to(cluster)

            m.fit_bounds([[miny, minx], [maxy, maxx]])

            #adds heatmap
            if show_heatmap:
                heat_data = gdf[["decimalLatitude", "decimalLongitude"]].dropna().values.tolist()
                if heat_data:
                    HeatMap(heat_data, radius=10, blur=15).add_to(m)

            folium.LayerControl().add_to(m)

            unique_species = gdf['commonName'].nunique()
            st.subheader(f"Showing {len(gdf)} total sightings across {unique_species} species")
            st_folium(m, width=1000, height=600)