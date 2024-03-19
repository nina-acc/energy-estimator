import streamlit as st
import plotly.graph_objects as go
import requests
import polyline
from math import radians, cos, sin, asin, sqrt
import requests

st.set_page_config(layout="wide")

def get_driving_distance_osrm(start_lat, start_lon, end_lat, end_lon):
    # Construct the request URL
    osrm_route_url = f"http://router.project-osrm.org/route/v1/driving/{start_lon},{start_lat};{end_lon},{end_lat}?overview=false"

    # Make the request to the OSRM API
    response = requests.get(osrm_route_url)
    if response.status_code == 200:
        data = response.json()

        # Extract the distance from the route summary
        distance = data['routes'][0]['distance']  # Distance in meters

        return distance
    else:

        return None


def haversine(lon1, lat1, lon2, lat2):
    """
    Calculate the great circle distance in kilometers between two points
    on the earth (specified in decimal degrees)
    """
    # Convert decimal degrees to radians
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])

    # Haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    r = 6371 # Radius of earth in kilometers. Use 3956 for miles
    return c * r

# Function to fetch elevation profile from OpenStreetMap API
def get_maxspeed_for_route(route_points):
    maxspeeds = []
    for point in route_points:
        lat, lon = point
        # Get the maxspeed from OSM API
        response = requests.get(f"https://api.openstreetmap.org/api/0.6/way/nearest?format=json&lat={lat}&lon={lon}")
        if response.status_code == 200:
            data = response.json()
            tags = data.get('tags', {})
            maxspeed = tags.get('maxspeed', '50')  # Default to 50 if maxspeed is not available
            try:
                maxspeed_int = int(maxspeed)
                maxspeeds.append(maxspeed_int)
            except ValueError:
                # Skip this maxspeed value if it cannot be converted to an integer
                pass
        else:
            print(f"Failed to fetch maxspeed data from OSM API: {response.status_code}")
    return maxspeeds

def categorize_traffic(maxspeeds):
    categories = []
    for maxspeed in maxspeeds:
        if maxspeed is None:
            categories.append(None)
        elif maxspeed <= 50:
            categories.append("city_traffic")
        elif 50 < maxspeed <= 100:
            categories.append("highway_traffic")
        else:
            categories.append("freeway_traffic")
    return categories

def get_elevation_profile(start_lat,start_lon, end_lat, end_lon):
    # Step 1: Get the route as a polyline from the OSRM API
    osrm_url = f"https://router.project-osrm.org/route/v1/driving/{start_lon},{start_lat};{end_lon},{end_lat}?overview=full&geometries=polyline"
    osrm_response = requests.get(osrm_url)
    if osrm_response.status_code != 200:
        print("Error fetching the route from OSRM")
        return [], []

    osrm_data = osrm_response.json()
    if 'routes' not in osrm_data or len(osrm_data['routes']) == 0:
        print("No routes found")
        return [], []

    route_polyline = osrm_data['routes'][0]['geometry']
    # Decode the polyline to get route points
    route_points = polyline.decode(route_polyline)

    # Step 2: Prepare the list of points for Open-Elevation API
    # Note: Depending on usage limits, you might need to sample this list
    locations = [{"latitude": lat, "longitude": lon} for lat, lon in route_points[::10]]  # Sampling every 10th point

    # Open-Elevation API endpoint
    open_elevation_url = "https://api.open-elevation.com/api/v1/lookup"
    response = requests.post(open_elevation_url, json={"locations": locations})
    if response.status_code != 200:
        print("Error fetching elevation data")
        return [], []

    elevation_data = response.json()
    if 'results' not in elevation_data:
        print("Elevation data not found in the response")
        return [], []


    # Calculate distances between consecutive points in meters
    distances = [0]  # Start with an initial distance of 0
    for i in range(1, len(locations)):
        prev_point = locations[i - 1]
        current_point = locations[i]
        distance_km = haversine(prev_point["longitude"], prev_point["latitude"],
                                current_point["longitude"], current_point["latitude"])
        distance_m = distance_km * 1000  # Convert km to meters
        distances.append(distances[-1] + distance_m)  # Cumulative distance

    # Extracting elevation and distance (assuming sequential points for simplicity)
    elevations = [result['elevation'] for result in elevation_data['results']]
  #distances = #HERE

    return distances, elevations
def get_elevation_profile_2(start_lat, start_lon, end_lat, end_lon):
    # Step 1: Get the route as a polyline from the OSRM API
    osrm_url = f"https://router.project-osrm.org/route/v1/driving/{start_lon},{start_lat};{end_lon},{end_lat}?overview=full&geometries=polyline"
    osrm_response = requests.get(osrm_url)
    if osrm_response.status_code != 200:
        print("Error fetching the route from OSRM")
        return [], []

    osrm_data = osrm_response.json()
    if 'routes' not in osrm_data or len(osrm_data['routes']) == 0:
        print("No routes found")
        return [], []

    route_polyline = osrm_data['routes'][0]['geometry']
    # Decode the polyline to get route points
    route_points = polyline.decode(route_polyline)

    # Step 2: Prepare the list of points for Open-Elevation API
    # Note: Depending on usage limits, you might need to sample this list
    locations = [{"latitude": lat, "longitude": lon} for lat, lon in route_points[::10]]  # Sampling every 10th point

    maxspeeds = get_maxspeed_for_route(route_points)
    print("Maxspeeds:", maxspeeds)  # Debugging
    # Categorize traffic based on maxspeeds
    traffic_categories = categorize_traffic(maxspeeds)
    print("Traffic categories:", traffic_categories)  # Debugging


    # Open-Elevation API endpoint
    open_elevation_url = "https://api.open-elevation.com/api/v1/lookup"
    response = requests.post(open_elevation_url, json={"locations": locations})
    if response.status_code != 200:
        print("Error fetching elevation data")
        return [], []

    elevation_data = response.json()
    if 'results' not in elevation_data:
        print("Elevation data not found in the response")
        return [], []

    # Calculate distances between consecutive points in meters
    distances = [0]  # Start with an initial distance of 0
    for i in range(1, len(locations)):
        prev_point = locations[i - 1]
        current_point = locations[i]
        distance_km = haversine(prev_point["longitude"], prev_point["latitude"],
                                current_point["longitude"], current_point["latitude"])
        distance_m = distance_km * 1000  # Convert km to meters
        distances.append(distances[-1] + distance_m)  # Cumulative distance

    # Extracting elevation (assuming sequential points for simplicity)
    elevations = [result['elevation'] for result in elevation_data['results']]

    return distances, elevations, traffic_categories

# Function to fetch autocomplete suggestions from Nominatim API
def get_autocomplete_results(query):
    url = f"https://nominatim.openstreetmap.org/search?format=json&q={query}"
    response = requests.get(url)
    data = response.json()
    return data


def get_gps_from_address(address):
    base_url = "https://nominatim.openstreetmap.org/search"
    params = {
        "q": address,
        "format": "json"
    }
    response = requests.get(base_url, params=params)
    data = response.json()
    if data:
        # Assuming the first result is the most relevant one
        return float(data[0]['lat']), float(data[0]['lon'])
    else:
        return None, None

# Example function to generate a Sankey diagram
def generate_sankey(slider1_value, slider2_value, slider3_value, slider4_value):
    # Example data for the Sankey diagram that uses slider values
    # Adjust this logic based on your specific data and how slider values should affect it
    node_labels = ["Node 0", "Node 1", "Node 2", "Node 3"]
    source_nodes = [0, 1, 0, 2, 3]
    target_nodes = [2, 3, 3, 0, 1]
    flow_values = [slider1_value, slider2_value, slider3_value, slider4_value, slider1_value + slider2_value]

    # Create the Sankey diagram
    fig = go.Figure(data=[go.Sankey(
        node=dict(
            pad=15,
            thickness=20,
            line=dict(color="black", width=0.5),
            label=node_labels,
        ),
        link=dict(
            source=source_nodes,
            target=target_nodes,
            value=flow_values
        ))])

    fig.update_layout(title_text="Dynamic Sankey Diagram", font_size=10)
    return fig

###-----setup
# Set up Streamlit UI
st.title('EV Energy and Consumption Estimator')

# Sidebar for address input and GPS coordinate retrieval
st.sidebar.title("Address Selection")

# Initialize session state to store selected addresses and coordinates
if 'selected_addresses' not in st.session_state:
    st.session_state.selected_addresses = {
        'departure': None,
        'destination': None
    }
if 'coordinates' not in st.session_state:
    st.session_state.coordinates = {
        'start_lat': None,
        'start_lon': None,
        'end_lat': None,
        'end_lon': None
    }

# Departure address autocomplete section
start_query = st.sidebar.text_input('Enter Departure Address', key="departure_address_input")
departure_address_placeholder = st.sidebar.empty()  # Placeholder for displaying selected departure address

if start_query:
    autocomplete_results_start = get_autocomplete_results(start_query)
    if autocomplete_results_start:
        st.sidebar.write("Autocomplete Suggestions for Departure Address:")
        for j, result_start in enumerate(autocomplete_results_start):
            if 'display_name' in result_start:
                address_start = result_start['display_name']
                if st.sidebar.button(f"Suggestion {j + 1}: {address_start}"):
                    st.session_state.selected_addresses['departure'] = address_start
                    st.session_state.coordinates['start_lat'], st.session_state.coordinates[
                        'start_lon'] = get_gps_from_address(address_start)

# Update departure address placeholder dynamically
if st.session_state.selected_addresses['departure']:
    departure_address_placeholder.text(
        f"Selected Departure Address: {st.session_state.selected_addresses['departure']}")

# Address autocomplete section for destination address
end_query = st.sidebar.text_input('Enter Destination Address', '')
destination_address_placeholder = st.sidebar.empty()

if end_query:
    autocomplete_results_end = get_autocomplete_results(end_query)
    if autocomplete_results_end:
        st.sidebar.write("Autocomplete Suggestions for Destination Address:")
        for i, result in enumerate(autocomplete_results_end):
            if 'display_name' in result:
                address_end = result['display_name']
                if st.sidebar.button(f"Suggestion {i + 1}: {address_end}"):
                    st.session_state.selected_addresses['destination'] = address_end
                    st.session_state.coordinates['end_lat'], st.session_state.coordinates[
                        'end_lon'] = get_gps_from_address(address_end)

# Update departure address placeholder dynamically
if st.session_state.selected_addresses['destination']:
    destination_address_placeholder.text(
        f"Selected Destination Address: {st.session_state.selected_addresses['destination']}")

# Get start and end coordinates from user input
start_lat_box = st.sidebar.number_input('Start Latitude', st.session_state.coordinates['start_lat'])
start_lon_box = st.sidebar.number_input('Start Longitude', st.session_state.coordinates['start_lon'])
end_lat_box = st.sidebar.number_input('End Latitude', st.session_state.coordinates['end_lat'])
end_lon_box = st.sidebar.number_input('End Longitude', st.session_state.coordinates['end_lon'])

# Initialize a key in the session state to track if the dashboard should be displayed
if 'show_dashboard' not in st.session_state:
    st.session_state.show_dashboard = False

# When the "Create Dashboard" button is clicked, set this state to True
if st.sidebar.button('Create Dashboard'):
    st.session_state.show_dashboard = True

# Check the session state to decide whether to show the dashboard
if st.session_state.show_dashboard:
    if st.session_state.selected_addresses['departure'] and st.session_state.selected_addresses['destination']:
        distances, elevations = get_elevation_profile(st.session_state.coordinates['start_lat'],
                                                      st.session_state.coordinates['start_lon'],
                                                      st.session_state.coordinates['end_lat'],
                                                      st.session_state.coordinates['end_lon'])

        if elevations:  # Checking if the list of elevations is not empty
            # Calculate net elevation change
            net_elevation_change = elevations[-1] - elevations[0]  # Elevation change from start to end

            #Get Driven (m)
            distance = get_driving_distance_osrm(st.session_state.coordinates['start_lat'],
                                                      st.session_state.coordinates['start_lon'],
                                                      st.session_state.coordinates['end_lat'],
                                                      st.session_state.coordinates['end_lon'])


            # Convert distances from range to list
            distances_list = list(distances)

            # Create elevation profile plot
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=distances_list, y=elevations, mode='lines', name='Elevation Profile'))
            fig.update_layout(title='Elevation Profile', xaxis_title='Distance (m)', yaxis_title='Elevation (m)')





        col1, col2, col3 = st.columns([1, 1,1])

        st.markdown("""
        <style>
        div.stContainer {
            border: 2px solid #4CAF50;
            border-radius: 10px;
            padding: 10px;
            margin-bottom: 20px;
        }
        </style>
        """, unsafe_allow_html=True)

        with col1: #user controls
            elevation_plot_c = st.container()  # First container in column 1
            info_route_c = st.container()  # Second container in column 1
            road_stats_c = st.container()

            with elevation_plot_c:
                st.plotly_chart(fig, use_container_width=True)

            with info_route_c:
                col1_1, col1_2= st.columns(2)
                col1_1.metric("Elevation Change ", f"{net_elevation_change}")
                col1_2.metric("Driving Distance Total ", f"{round(distance / 1000)} km")

            with road_stats_c:
                urban = 30
                rural = 30
                motorway = 40

                col1_11, col1_21, col1_23= st.columns(3)
                col1_11.metric("Urban roads ", f"{urban} %")
                col1_21.metric("Rural roads ", f"{rural} %")
                col1_23.metric("Motorway roads ", f"{motorway} %")

        with col2:#elevation and route
                # Sliders
                battery_size = st.slider('Battery Size [kWh]:', min_value=40, max_value=100, value=70, step=10)
                tire_pressure = st.toggle('Low Tire Pressure')
                st.divider()

                heater = st.slider('Heater:', min_value=0, max_value=4, value=2, step=1)
                air_conditioning = st.slider('Air Conditioning:', min_value=0, max_value=4, value=0, step=1)
                avg_speed_city = st.slider('Average Speed City Traffic [km/h]:', min_value=0, max_value=250, value=50)
                avg_speed_landstraße = st.slider('Average Speed Highway (~Landstraße) Traffic [km/h]:', min_value=0,
                                                 max_value=250, value=50)
                avg_speed_autobahn = st.slider('Average Speed Freeway (~Autobahn) Traffic [km/h]:', min_value=0,
                                               max_value=250, value=50)

        # Assuming col2 and col3 setup above is correct and sliders are defined in col2

        with col3:  # Sankey diagram
            sankey_plot_c = st.container()  # First container in column 1
            range_route_c = st.container()  # Second container in column 1

            with sankey_plot_c:
                # Define labels for all nodes (including the battery as the target)
                labels = ["Heater", "Air Con", "Avg Speed City", "Avg Speed Highway", "Battery Size"]

                # Define source nodes (indexes from labels list)
                source = [0, 1, 2, 3]  # Heater, Air Con, Avg Speed City, Avg Speed Highway

                # Define target nodes (indexes from labels list pointing to Battery Size)
                target = [4, 4, 4, 4]  # All flow to "Battery Size"

                # Use the slider values as the flow values
                value = [heater, air_conditioning, avg_speed_city, avg_speed_landstraße]

                # Create Sankey diagram
                fig_sankey = go.Figure(data=[go.Sankey(
                    node=dict(
                        pad=15,
                        thickness=20,
                        line=dict(color="black", width=0.5),
                        label=labels,
                    ),
                    link=dict(
                        source=source,
                        target=target,
                        value=value
                    ))])

                fig_sankey.update_layout(title_text="Dynamic Sankey Diagram", font_size=10)
                st.plotly_chart(fig_sankey, use_container_width=True)
        with range_route_c:
            col3_1, col3_2 = st.columns(2)
            col3_1.metric("Estimated Energy Consumption ", f"{net_elevation_change} kWh")
            col3_2.metric("Estimated Range under given Conditions ", f"{round(distance / 1000)} km")


    else:
            st.error('Failed to fetch elevation profile. Please check your input coordinates.')
else:
    st.error('Please select both departure and destination addresses.')