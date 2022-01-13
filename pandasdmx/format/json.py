"""Information about the SDMX-JSON file format."""
from pandasdmx.format import list_content_types

#: Known media types for SDMX-JSON.
CONTENT_TYPES = [
    # Older files
    "application/vnd.sdmx.draft-sdmx-json+json",
    # For e.g. OECD
    "draft-sdmx-json",
    "text/json",
] + list_content_types(base="json")
