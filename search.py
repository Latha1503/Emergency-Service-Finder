
import requests
from geopy.distance import geodesic


def search_services(latitude, longitude, category, radius=3000):

    urls = [
        "https://overpass-api.de/api/interpreter",
        "https://overpass.kumi.systems/api/interpreter"
    ]

    categories = {
        "Hospital": ("amenity", "hospital"),
        "Pharmacy": ("amenity", "pharmacy"),
        "Police Station": ("amenity", "police"),
        "Fire Station": ("amenity", "fire_station")
    }

    if category not in categories:
        raise ValueError("Invalid service category")

    tag, value = categories[category]

    query = f"""
    [out:json][timeout:25];
    (
        node["{tag}"="{value}"](around:{radius},{latitude},{longitude});
        way["{tag}"="{value}"](around:{radius},{latitude},{longitude});
        relation["{tag}"="{value}"](around:{radius},{latitude},{longitude});
    );
    out center tags;
    """

    data = None

    for url in urls:
        try:
            response = requests.post(
                url,
                data={"data": query},
                headers={
                    "User-Agent": "EmergencyServiceFinder/1.0",
                    "Accept": "application/json"
                },
                timeout=(10, 45)
            )

            response.raise_for_status()
            data = response.json()
            break

        except requests.RequestException as e:
            print("API server failed:", url, e)

        except ValueError as e:
            print("Invalid JSON response:", e)

    if data is None:
        raise Exception(
            "Overpass API servers are unavailable. "
            "Please try again later."
        )

    services = []

    for item in data.get("elements", []):

        tags = item.get("tags", {})

        if "lat" in item:
            lat = item["lat"]
            lon = item["lon"]

        elif "center" in item:
            lat = item["center"]["lat"]
            lon = item["center"]["lon"]

        else:
            continue

        distance = geodesic(
            (latitude, longitude),
            (lat, lon)
        ).km

        services.append({
            "name": tags.get("name", "Name not available"),
            "category": category,
            "latitude": lat,
            "longitude": lon,
            "distance": round(distance, 2),
            "phone": tags.get("phone", "Not available"),
            "address": tags.get("addr:full", "Not available")
        })

    services.sort(key=lambda x: x["distance"])

    return services
