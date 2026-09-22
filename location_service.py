from geopy.geocoders import Nominatim


geolocator = Nominatim(user_agent="agrilinkai")


def get_location_from_coordinates(
    latitude: float,
    longitude: float
) -> str:
    """
    Convert GPS coordinates into a city/location name.
    """

    try:
        location = geolocator.reverse(
            (latitude, longitude),
            language="en"
        )

        if not location:
            return "Unknown"

        address = location.raw.get("address", {})

        city = (
            address.get("city")
            or address.get("town")
            or address.get("village")
            or address.get("county")
        )

        state = address.get("state")

        if city and state:
            return f"{city}, {state}"

        if city:
            return city

        return "Unknown"

    except Exception:
        return "Unknown"