import streamlit as st
import google.generativeai as genai
from PIL import Image
import pandas as pd
import folium
from streamlit_folium import st_folium
import os
import json

st.set_page_config(page_title="GeoShield AI", page_icon="🛡️", layout="wide")

# API Setup
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

# Session State for Incident Storage
if "incidents" not in st.session_state:
    st.session_state.incidents = [
        {
            "id": 1,
            "title": "Severe Waterlogging & Road Block",
            "category": "Flood / Drainage",
            "severity": "High",
            "lat": 19.1383,
            "lon": 77.3210,
            "status": "Under Review"
        }
    ]

# Sidebar Navigation
st.sidebar.title("🛡️ GeoShield AI")
st.sidebar.caption("Multimodal Disaster & Hazard Response Agent")
role = st.sidebar.radio("Select Portal View", ["Citizen Reporter", "Authority Command Center"])

# --- CITIZEN VIEW ---
if role == "Citizen Reporter":
    st.header("📢 Report a Public Hazard or Emergency")
    st.write("Upload an incident photo. Gemini Multimodal Vision will inspect and triage the hazard.")

    uploaded_file = st.file_uploader("Upload Incident Photo (JPG/PNG)", type=["jpg", "jpeg", "png"])
    
    col1, col2 = st.columns(2)
    with col1:
        latitude = st.number_input("Incident Latitude", value=19.1500, format="%.4f")
    with col2:
        longitude = st.number_input("Incident Longitude", value=77.3100, format="%.4f")

    if uploaded_file and st.button("Analyze & Dispatch Alert", type="primary"):
        image = Image.open(uploaded_file)
        st.image(image, caption="Uploaded Image", use_container_width=True)

        with st.spinner("Gemini 1.5 Flash analyzing visual hazard..."):
            try:
                model = genai.GenerativeModel("gemini-1.5-flash")
                prompt = (
                    "Analyze this emergency or infrastructure hazard image. "
                    "Return ONLY a clean JSON object with the following keys: "
                    "'hazard_type' (short name), 'severity' (Low, Medium, High, or Critical), "
                    "'action_required' (one sentence), and 'triage_summary' (two sentences)."
                )
                response = model.generate_content([prompt, image])
                clean_text = response.text.replace("```json", "").replace("```", "").strip()
                data = json.loads(clean_text)

                st.success("✅ Hazard Categorized by Gemini Vision!")
                st.json(data)

                # Save incident
                new_incident = {
                    "id": len(st.session_state.incidents) + 1,
                    "title": data.get("hazard_type", "Hazard Alert"),
                    "category": data.get("hazard_type", "General"),
                    "severity": data.get("severity", "Medium"),
                    "lat": latitude,
                    "lon": longitude,
                    "status": "Dispatched"
                }
                st.session_state.incidents.append(new_incident)
                st.info("Incident geotagged and synced to response queue.")
            except Exception as e:
                st.warning(f"Analysis logged locally: {e}")

# --- AUTHORITY COMMAND CENTER ---
else:
    st.header("🚨 Authority Command & Triage Center")
    st.write("Live spatial visualization of reported incidents.")

    df = pd.DataFrame(st.session_state.incidents)
    
    # Metrics
    m1, m2, m3 = st.columns(3)
    m1.metric("Total Incidents", len(df))
    m2.metric("Critical / High", len(df[df['severity'].isin(['High', 'Critical'])]))
    m3.metric("Pending Response", len(df[df['status'] == 'Dispatched']))

    # Interactive Map
    st.subheader("Geographical Incident Cluster")
    m = folium.Map(location=[19.1400, 77.3200], zoom_start=13)
    for _, row in df.iterrows():
        color = "red" if row["severity"] in ["High", "Critical"] else "orange"
        folium.Marker(
            location=[row["lat"], row["lon"]],
            popup=f"{row['title']} ({row['severity']})",
            icon=folium.Icon(color=color, icon="info-sign")
        ).add_to(m)
    st_folium(m, width=900, height=450)

    st.subheader("Active Incidents Queue")
    st.dataframe(df, use_container_width=True)
          
