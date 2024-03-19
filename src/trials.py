import requests

def get_road_classification(latitude, longitude):
    url = f"https://nominatim.openstreetmap.org/reverse?format=json&lat={latitude}&lon={longitude}"
    response = requests.get(url)
    data = response.json()
    road_tags = data.get('address', {}).get('road', '')

    print(road_tags)
    # Classify road based on tags
    if "motorway" in road_tags:
        return "Motorway"
    elif "residential" in road_tags:
        return "Urban"
    else:
        return "Rural"

# Example GPS points (latitude, longitude)
gps_points = [
    (52.5200, 13.4050),  # Berlin, Germany
    (40.7128, -74.0060), # New York City, USA
    (34.0522, -118.2437) # Los Angeles, USA
]

# Get road classification for each GPS point
road_classifications = [get_road_classification(lat, lon) for lat, lon in gps_points]

# Print the classifications
for i, classification in enumerate(road_classifications):
    print(f"GPS Point {i+1}: {classification}")

