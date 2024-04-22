import streamlit as st
import plotly.graph_objects as go
import requests
import polyline
from math import radians, cos, sin, asin, sqrt
import requests
import folium
from folium.plugins import MarkerCluster

if 'sidebar_state' not in st.session_state:
    st.session_state.sidebar_state = 'expanded'

st.set_page_config(layout="wide", initial_sidebar_state=st.session_state.sidebar_state)



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

def get_elevation_profile(start_lat,start_lon, end_lat, end_lon):
    print("Start GPS Point:", start_lat, start_lon)
    print("End GPS Point:", end_lat, end_lon)
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
    # Note: resampled to 100 due to limited access to API; tried with 10 before - did not work consistently
    locations = [{"latitude": lat, "longitude": lon} for lat, lon in route_points[::100]]  # Sampling every 10th point

    # Open-Elevation API endpoint
    open_elevation_url = "https://api.open-elevation.com/api/v1/lookup"
    response = requests.post(open_elevation_url, json={"locations": locations})
    if response.status_code != 200:
        print("Error fetching elevation data")
        return [], [], []

    elevation_data = response.json()
    if 'results' not in elevation_data:
        print("Elevation data not found in the response")
        return [], [],[]


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
    return distances, elevations, route_points

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
        return float(data[0]['lat']), float(data[0]['lon'])
    else:
        return None, None

def generate_bar_view(heater, air_conditioning, avg_speed, tire_pressure, elevation, distance, temperature):
    # Berechnet Verbrauchswerte für jedes Eingabefeld
    (total_consumption, heater_v, air_conditioning_v, avg_speed_v, net_elevation_change_v, distance_v, tire_pressure_v,
     oat_v) = get_consumption(elevation, distance/1000, heater, air_conditioning, avg_speed, tire_pressure, temperature)

    # Prüft, ob der Gesamtverbrauch größer als 0 ist, um Division durch Null zu vermeiden

    consumption_heater = heater_v / total_consumption * 100
    consumption_air_conditioning = air_conditioning_v / total_consumption * 100
    consumption_avg_speed = avg_speed_v / total_consumption * 100
        # Stellt sicher, dass tire_pressure_v ein Prozentwert ist
    consumption_tire_pressure = tire_pressure_v * 100 if tire_pressure else 0
    consumption_elevation = net_elevation_change_v / total_consumption * 100
    consumption_temperature = oat_v / total_consumption * 100


    # Fasst alle Verbrauchswerte zusammen
    consumption_values = [consumption_heater, consumption_air_conditioning, consumption_avg_speed,
                          consumption_tire_pressure, consumption_elevation, consumption_temperature]

    return consumption_values

# def generate_bar_view(heater, air_conditioning, avg_speed, tire_pressure, elevation, distance, temperature):
#     # Calculate consumption values for each input field
#     total_consumption, heater_v, air_conditioning_v, avg_speed_v, net_elevation_change_v, distance_v, tire_pressure_v, oat_v = get_consumption(
#         elevation, distance / 1000, heater, air_conditioning, avg_speed, tire_pressure, temperature)
#
#     # Return consumption values in kWh
#     return [heater_v, air_conditioning_v, avg_speed_v, tire_pressure_v, net_elevation_change_v, oat_v]
#


# Function to plot OSM map with data points
def plot_osm_map(start_lat, start_lon, end_lat, end_lon, route_points):
    # Create a folium map centered at the mean of start and end coordinates
    m = folium.Map(location=[(start_lat + end_lat) / 2, (start_lon + end_lon) / 2], zoom_start=10)

    # Add a PolyLine representing the route
    folium.PolyLine(locations=route_points, color='blue').add_to(m)

    # Fit the map to the bounds of the route line
    m.fit_bounds([[min([lat for lat, lon in route_points]), min([lon for lat, lon in route_points])],
                  [max([lat for lat, lon in route_points]), max([lon for lat, lon in route_points])]])

    return m


def get_consumption(net_elevation_change, distance, heater, air_conditioning, avg_speed, tire_pressure, temperature):


    # model is based on cubic transformation of target
    intercept =  0.6113081001055111
    #weight_speed = -0.006926
    weight_elevation =  0.0023704721443417744
    weight_distance =  0.05318775764140953
    weight_speed = (-0.0006027077642036938)
    weight_oat =  (-0.0026105994749679594)
    weight_heater =  0.4256478572412367
    weight_air_conditioning =  0.5208677407916299



    heater_v = (heater/1000)*(distance/avg_speed)*weight_heater
    print("h", heater_v)

    air_conditioning_v = (air_conditioning/1000)*(distance/avg_speed)*weight_air_conditioning
    print("ac", air_conditioning_v)
    avg_speed_v = (avg_speed)*(weight_speed)
    net_elevation_change_v = net_elevation_change*weight_elevation
    distance_v = distance*weight_distance
    oat_v = (temperature)*(weight_oat)
    print("oat", oat_v)



    if(tire_pressure):
        total_consumption = ((intercept+avg_speed_v+air_conditioning_v+heater_v+net_elevation_change_v+distance_v+oat_v)**3)*1.3
        tire_pressure_v = ((intercept+avg_speed_v+air_conditioning_v+heater_v+net_elevation_change_v+distance_v+oat_v)**3)*0.3
    else:
        total_consumption = (intercept + avg_speed_v + air_conditioning_v + heater_v + net_elevation_change_v + distance_v +oat_v)**3
        tire_pressure_v = 0.0

    return total_consumption, heater_v, air_conditioning_v, avg_speed_v, net_elevation_change_v, distance_v, tire_pressure_v, oat_v
# Function to enable disabling the sidebar
#def toggle_sidebar_state():
 #   st.session_state.sidebar_state = 'collapsed' if st.session_state.sidebar_state == 'expanded' else 'expanded'
    # Set query parameters to trigger a rerun with the updated session state
    #st.set_query_params(sidebar_state=st.session_state.sidebar_state)

# Initialize a session state variable that tracks the sidebar state (either 'expanded' or 'collapsed').
if 'sidebar_state' not in st.session_state:
    st.session_state.sidebar_state = 'expanded'


###-----setup
# Set up Streamlit UI
st.title('EV Energy and Consumption Estimator')

#Update button placeholder
#update_button_placeholder = st.empty()
# Condition to determine whether to show the button
#show_update_button = False




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
    st.session_state.sidebar_state = 'collapsed' if st.session_state.sidebar_state == 'expanded' else 'expanded'
    # Force an app rerun after switching the sidebar state.
    st.session_state.show_dashboard = True
    #show_update_button = True
    st.experimental_rerun()


# Check the sidebar state to decide whether to show the sidebar
if st.session_state.sidebar_state == 'collapsed':
    st.markdown("""
        <style>
            .sidebar .sidebar-content {
                display: none;
            }
        </style>
    """, unsafe_allow_html=True)

# Check the session state to decide whether to show the dashboard
if st.session_state.show_dashboard:
    #st.session_state.sidebar_state = 'collapsed'
    if st.session_state.sidebar_state == 'collapsed':
        # Hide the sidebar using custom CSS
        st.markdown("""
                <style>
                    .sidebar .sidebar-content {
                        display: none;
                    }
                    .block-container {
                        width: 100%;
                    }
                </style>
            """, unsafe_allow_html=True)
    if st.session_state.selected_addresses['departure'] and st.session_state.selected_addresses['destination']:
        distances, elevations, route_points = get_elevation_profile(st.session_state.coordinates['start_lat'],
                                                      st.session_state.coordinates['start_lon'],
                                                      st.session_state.coordinates['end_lat'],
                                                      st.session_state.coordinates['end_lon'])
        fig = go.Figure()
        if elevations:  # Checking if the list of elevations is not empty

            #Create button to update
            #update_button = st.button("Update Dashboard")

            # Calculate net elevation change
            net_elevation_change = 0
            net_elevation_change = elevations[-1] - elevations[0]  # Elevation change from start to end

            #Get Driven (m)
            distance = get_driving_distance_osrm(st.session_state.coordinates['start_lat'],
                                                      st.session_state.coordinates['start_lon'],
                                                      st.session_state.coordinates['end_lat'],
                                                      st.session_state.coordinates['end_lon'])


            # Convert distances from range to list
            distances_list = list(distances)

            # Create elevation profile plot
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
            map_c = st.container()  # First container in column 1
            info_route_c = st.container()  # Second container in column 1

            with map_c:
                st.header("Route Details")
                #st.plotly_chart(fig, use_container_width=True)
                if route_points:
                    folium_map = plot_osm_map(st.session_state.coordinates['start_lat'],
                                              st.session_state.coordinates['start_lon'],
                                              st.session_state.coordinates['end_lat'],
                                              st.session_state.coordinates['end_lon'], route_points)

                    folium_map.save("map.html")
                    st.components.v1.html(open("map.html", 'r').read(), width=500, height=500)
                else:
                    st.error('Failed to fetch route points. Please check your input coordinates.')

            with info_route_c:
                col1_1, col1_2= st.columns(2)
                col1_1.metric("Elevation Change ", f"{net_elevation_change}")
                col1_2.metric("Driving Distance Total ", f"{round(distance / 1000)} km")

        with col2:#elevation and route
            st.header("Input Parameters")
            # Sliders
            battery_size = st.slider('Battery Size [kWh]:', min_value=40, max_value=100, value=70, step=10)
            temperature = st.slider('Temperature [C°]:', min_value=-20, max_value=40, value=10, step=1)
            tire_pressure = st.toggle('Low Tire Pressure')
            st.divider()

            heater = st.slider('Heater [W]:', min_value=0, max_value=4000, value=200, step=100)
            air_conditioning = st.slider('Air Conditioning [W]:', min_value=0, max_value=1600, value=200, step=100)
            avg_speed = st.slider('Average Speed [km/h]:', min_value=0, max_value=250, value=50)


        # Assuming col2 and col3 setup above is correct and sliders are defined in col2
        (total_consumption, heater_v, air_conditioning_v, avg_speed_v, net_elevation_change_v, distance_v,
         tire_pressure_v, temperature_v) = get_consumption(net_elevation_change,distance/1000,heater,air_conditioning,avg_speed,tire_pressure, temperature)

        with col3:  # Sankey diagram
            st.header("Consumption per Input Variable")
            bar_plot_c = st.container()  # First container in column 1
            range_route_c = st.container()  # Second container in column 1

            with bar_plot_c:
                consumption_values = generate_bar_view(heater, air_conditioning, avg_speed, tire_pressure,
                                                       net_elevation_change, distance/1000, temperature)

                # Define sources for the bar chart
                sources = ['Heater', 'Air Conditioning', 'Average Speed', 'Tire Pressure', 'Elevation', 'Temperature']

                # Create individual bar traces for each source
                individual_traces = go.Bar(x=sources, y=consumption_values, name='Consumption',
                                           marker=dict(color='blue'),
                                           text=[f"{val:.2f}%" for val in consumption_values],
                                           # Text to display on top of bars
                                           textposition='auto')  # Automatically position the text

                # Create layout
                layout = go.Layout(
                    xaxis=dict(title='Sources', tickangle=45, tickmode='array', tickvals=sources, ticktext=sources),
                    yaxis=dict(title='Consumption (%)'),
                    legend=dict(x=0, y=1.0, bgcolor='rgba(255, 255, 255, 0)'),
                    font=dict(size=16)
                )

                # Create figure
                fig = go.Figure(data=[individual_traces], layout=layout)

                fig.update_traces(
                    hoverinfo='y',
                    hovertemplate='%{y:.2f}%',
                    hoverlabel=dict(
                        font=dict(size=32)
                    )
                )
                st.plotly_chart(fig, use_container_width=True)

        with range_route_c:
            #consumption=get_consumption(net_elevation_change,distance/1000,heater,air_conditioning,avg_speed,tire_pressure)
            col3_1, col3_2 = st.columns(2)
            col3_1.metric("Estimated Energy Consumption ", f"{round(total_consumption,4)} kWh")
            col3_1.metric("Estimated kWh/100km ", f"{round((total_consumption/(distance/1000))*100, 4)}")
            col3_2.metric("Estimated Range ", f"{round((battery_size/(total_consumption/(distance/1000))),2)} km")
            #col3_2.metric("Estimated Range ", f"{round(battery_size / 1)} km")

        #for widget in [battery_size, tire_pressure, heater, air_conditioning, avg_speed_city, avg_speed_landstraße,
                       #avg_speed_autobahn, weight]:
            #widget.on_change(get_consumption(net_elevation_change, distance, heater,
                                                               # air_conditioning, avg_speed_city, avg_speed_landstraße,
                                                               # avg_speed_autobahn, tire_pressure, weight))


    else:
            st.error('Failed to fetch elevation profile. Please check your input coordinates.')
else:
    st.error('Please select both departure and destination addresses before pressing the button at the bottom.')


