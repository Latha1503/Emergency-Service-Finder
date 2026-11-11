
import streamlit as st
import folium
from streamlit_folium import st_folium

from location import get_coordinates
from search import search_services


# ---------------- PAGE CONFIGURATION ----------------

st.set_page_config(
    page_title="Emergency Service Finder",
    page_icon="🚑",
    layout="wide"
)


# ---------------- CUSTOM CSS ----------------

st.markdown("""
<style>
    .main {
        background-color: #f5f8fc;
    }

    .title {
        color: #12345a;
        font-size: 34px;
        font-weight: bold;
    }

    .subtitle {
        color: #64748b;
        font-size: 16px;
    }
</style>
""", unsafe_allow_html=True)


# ---------------- SESSION STATE ----------------

if "results" not in st.session_state:
    st.session_state.results = None

if "location" not in st.session_state:
    st.session_state.location = None

if "category" not in st.session_state:
    st.session_state.category = None

if "searched_place" not in st.session_state:
    st.session_state.searched_place = None

if "radius" not in st.session_state:
    st.session_state.radius = 3000


# ---------------- DASHBOARD HEADING ----------------

st.markdown(
    '<div class="title">🚑 Emergency Service Finder</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="subtitle">'
    'Find nearby hospitals, pharmacies, police stations '
    'and fire stations.'
    '</div>',
    unsafe_allow_html=True
)

st.write("")


# ---------------- SEARCH INPUTS ----------------

st.subheader("Find Emergency Services")

col1, col2 = st.columns(2)

with col1:
    place = st.text_input(
        "Enter your location",
        placeholder="Example: Gachibowli, Hyderabad"
    )

with col2:
    category = st.selectbox(
        "Select Emergency Service",
        [
            "Hospital",
            "Pharmacy",
            "Police Station",
            "Fire Station"
        ]
    )


# ---------------- SEARCH RADIUS ----------------

radius = st.select_slider(
    "Search radius",
    options=[1000, 3000, 5000, 10000],
    value=3000,
    format_func=lambda x: f"{x // 1000} km"
)


# ---------------- SEARCH BUTTON ----------------

if st.button("🔍 Search Nearby Services", use_container_width=True):

    if not place.strip():
        st.warning("Please enter your location.")

    else:
        try:
            with st.spinner("Finding nearby emergency services..."):

                # Convert entered place into coordinates
                location = get_coordinates(place)

                if location is None:
                    st.session_state.results = None
                    st.session_state.location = None
                    st.error(
                        "Location not found. Please enter another place."
                    )

                else:
                    latitude, longitude = location

                    # Search nearby emergency services
                    results = search_services(
                        latitude,
                        longitude,
                        category,
                        radius
                    )

                    # Save search information
                    st.session_state.results = results
                    st.session_state.location = location
                    st.session_state.category = category
                    st.session_state.searched_place = place
                    st.session_state.radius = radius

        except Exception as e:
            st.session_state.results = None
            st.error(f"Something went wrong: {e}")


# ---------------- DISPLAY RESULTS ----------------

if st.session_state.results is not None:

    results = st.session_state.results

    latitude, longitude = st.session_state.location

    saved_category = st.session_state.category
    saved_radius = st.session_state.radius
    saved_place = st.session_state.searched_place

    st.divider()

    # Search summary
    st.subheader("📊 Search Summary")

    st.caption(
        f"Showing results for the last completed search: {saved_place}"
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Services Found",
            len(results)
        )

    with col2:
        st.metric(
            "Search Radius",
            f"{saved_radius // 1000} km"
        )

    with col3:
        st.metric(
            "Service Type",
            saved_category
        )


    # ---------------- MAP ----------------

    st.subheader("📍 Nearby Services Map")

    # Create map centered on entered location
    map_object = folium.Map(
        location=[latitude, longitude],
        zoom_start=14,
        control_scale=True
    )

    # User location marker
    folium.Marker(
        location=[latitude, longitude],
        popup=f"Your Location: {saved_place}",
        tooltip="Your Location",
        icon=folium.Icon(
            color="blue",
            icon="home"
        )
    ).add_to(map_object)

    # Draw search radius circle
    folium.Circle(
        location=[latitude, longitude],
        radius=saved_radius,
        color="blue",
        fill=True,
        fill_color="blue",
        fill_opacity=0.08,
        tooltip=f"Search Radius: {saved_radius // 1000} km"
    ).add_to(map_object)

    # Service marker colors
    service_colors = {
        "Hospital": "red",
        "Pharmacy": "green",
        "Police Station": "blue",
        "Fire Station": "orange"
    }

    service_icons = {
        "Hospital": "plus-sign",
        "Pharmacy": "plus",
        "Police Station": "shield",
        "Fire Station": "fire"
    }

    # Add service markers
    for index, service in enumerate(results):

        # Highlight nearest service
        if index == 0:
            marker_color = "green"
            marker_icon = "star"
            marker_name = "Nearest Service"

        else:
            marker_color = service_colors[saved_category]
            marker_icon = service_icons[saved_category]
            marker_name = service["name"]

        folium.Marker(
            location=[
                service["latitude"],
                service["longitude"]
            ],
            popup=(
                f"{marker_name}: {service['name']} "
                f"({service['distance']} km)"
            ),
            tooltip=marker_name,
            icon=folium.Icon(
                color=marker_color,
                icon=marker_icon
            )
        ).add_to(map_object)

    # Fit map around user location and services
    if results:

        locations = [
            [latitude, longitude]
        ]

        for service in results:
            locations.append([
                service["latitude"],
                service["longitude"]
            ])

        map_object.fit_bounds(locations)

    # Display map
    st_folium(
        map_object,
        width=None,
        height=450,
        key="emergency_map"
    )


    # ---------------- SERVICE DETAILS ----------------

    st.subheader("🏥 Available Services")

    if results:

        # Show nearest service
        nearest = results[0]

        st.success(
            f"Nearest service: {nearest['name']} "
            f"({nearest['distance']} km away)"
        )

        # Display all services
        for index, service in enumerate(results, start=1):

            with st.container(border=True):

                if index == 1:
                    st.markdown("⭐ **NEAREST SERVICE**")

                st.markdown(
                    f"### {index}. {service['name']}"
                )

                col1, col2 = st.columns(2)

                with col1:

                    st.write(
                        f"📍 Distance: **{service['distance']} km**"
                    )

                    st.write(
                        f"📞 Phone: {service['phone']}"
                    )

                with col2:

                    st.write(
                        f"🏠 Address: {service['address']}"
                    )

                    # Google Maps directions
                    maps_url = (
                        "https://www.google.com/maps/dir/?api=1"
                        f"&destination={service['latitude']},"
                        f"{service['longitude']}"
                    )

                    st.link_button(
                        "🗺️ Get Directions",
                        maps_url
                    )

    else:

        st.warning(
            "No services found within this search radius. "
            "Try increasing the radius or changing the location."
        )


# ---------------- FOOTER ----------------

st.divider()

st.caption(
    "Emergency Service Finder | Uses OpenStreetMap data. "
    "Always verify facility availability and contact details."
)
