from sklearn.preprocessing import RobustScaler

def estimate_fuel_consumption(importances, features):
    # Assign weights to features based on their importances
    weights = {
        "distance": importances["Distance_over_interval[km]"],
        "generalized_weight": importances["Generalized_Weight"],
        "share_motorway": importances["Share_motorway_roads[%]"],
        "share_urban": importances["Share_urban_roads[%]"],
        "share_rural": importances["Share_rural_roads[%]"],
        "vehicle_speed": importances["Vehicle Speed[km/h]"],
        "gradients": importances["Gradients[m]"]
    }

    # Define the RobustScaler with the same parameters used during training
    robust_scaler = RobustScaler()

    # Scale the input features using the RobustScaler
    scaled_features = robust_scaler.transform([list(features.values())])

    # Extract the scaled values from the scaled features
    scaled_values = scaled_features[0]

    # Calculate the weighted sum of features
    weighted_sum = sum(weights[feature] * scaled_value for feature, scaled_value in zip(features.keys(), scaled_values))

    return weighted_sum


# Example usage
importances = {
    "Distance_over_interval[km]": 0.919261,
    "Generalized_Weight": 0.044579,
    "Share_motorway_roads[%]": 0.013086,
    "Share_urban_roads[%]": 0.011324,
    "Share_rural_roads[%]": 0.005960,
    "Vehicle Speed[km/h]": 0.004037,
    "Gradients[m]": 0.001753
}

# Example feature values
features = {
    "distance": 100.0,  # Distance in km
    "generalized_weight": 5000.0,  # Generalized weight
    "share_motorway": 0.3,  # Percentage of motorway roads
    "share_urban": 0.4,  # Percentage of urban roads
    "share_rural": 0.3,  # Percentage of rural roads
    "vehicle_speed": 80.0,  # Vehicle speed in km/h
    "gradients": 10.0  # Gradients in meters
}

# Estimate fuel consumption
estimated_consumption = estimate_fuel_consumption(importances, features)
print("Estimated fuel consumption:", estimated_consumption)
