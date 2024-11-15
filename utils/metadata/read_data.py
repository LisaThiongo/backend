from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS

async def extract_sensitive_metadata(image: Image):
    """
    Extract sensitive metadata such as camera model, geolocation, user information (owner name, software), 
    and other technical details from an image, without aperture, ISO, or shutter speed.
    """
    def to_degrees(value):
        """Convert GPS coordinates to degrees."""
        d, m, s = value
        return d + (m / 60.0) + (s / 3600.0)

    exifdata = image._getexif()
    if exifdata is None:
        return None  # No EXIF data found

    # Initialize variables for sensitive data
    model = None
    latitude, longitude = None, None
    owner_name = None
    software_used = None
    ip_address = None

    for tagid, value in exifdata.items():
        tagname = TAGS.get(tagid, tagid)

        # Extract device information
        if tagname == "Model":
            model = value
        elif tagname == "Software":
            software_used = value
        elif tagname == "Artist":
            owner_name = value

        # Extract GPS information for geolocation
        elif tagname == "GPSInfo":
            gps_info = {GPSTAGS.get(t, t): v for t, v in value.items()}
            lat = gps_info.get("GPSLatitude")
            lat_ref = gps_info.get("GPSLatitudeRef")
            lon = gps_info.get("GPSLongitude")
            lon_ref = gps_info.get("GPSLongitudeRef")

            if lat and lat_ref and lon and lon_ref:
                latitude = to_degrees(lat)
                longitude = to_degrees(lon)

                if lat_ref != "N":
                    latitude = -latitude
                if lon_ref != "E":
                    longitude = -longitude

        # Extract IP Address if available (usually from network metadata or file system)
        # Note: IP address isn't typically part of EXIF, so you'd need specific device or app handling for this.
        elif tagname == "IPAddress":
            ip_address = value

    return {
        "model": model,
        "geolocation": (latitude, longitude) if latitude and longitude else None,
        "owner_name": owner_name,
        "software_used": software_used,
        "ip_address": ip_address,
    }




# from PIL import Image
# from PIL.ExifTags import TAGS, GPSTAGS

# async def extract_sensitive_metadata(image: Image):
#     """
#     Extract sensitive metadata such as camera model and geolocation from an image.
#     """
#     def to_degrees(value):
#         """Convert GPS coordinates to degrees."""
#         d, m, s = value
#         return d + (m / 60.0) + (s / 3600.0)

#     exifdata = image._getexif()
#     if exifdata is None:
#         return None  # No EXIF data found

#     model = None
#     latitude, longitude = None, None

#     for tagid, value in exifdata.items():
#         tagname = TAGS.get(tagid, tagid)

#         if tagname == "Model":
#             model = value
#         elif tagname == "GPSInfo":
#             gps_info = {GPSTAGS.get(t, t): v for t, v in value.items()}
#             lat = gps_info.get("GPSLatitude")
#             lat_ref = gps_info.get("GPSLatitudeRef")
#             lon = gps_info.get("GPSLongitude")
#             lon_ref = gps_info.get("GPSLongitudeRef")

#             if lat and lat_ref and lon and lon_ref:
#                 latitude = to_degrees(lat)
#                 longitude = to_degrees(lon)

#                 if lat_ref != "N":
#                     latitude = -latitude
#                 if lon_ref != "E":
#                     longitude = -longitude

#     return {
#         "model": model,
#         "geolocation": (latitude, longitude) if latitude and longitude else None,
#     }


