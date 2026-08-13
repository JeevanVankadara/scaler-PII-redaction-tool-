"""Indian cities, by list.

The model tags a city as a place in one sentence and misses it in the next, and
misses it entirely inside an address line where there is no sentence structure
to go on. Address components were the weakest recall in the evaluation, and a
list is the honest way to fix that.

This is a stated domain assumption, not general behaviour: the document is an
Indian filing. Working somewhere else means changing this list.
"""

import re

from . import register
from .base import RegexRecognizer

CITIES = (
    "Ahmedabad", "Ahmednagar", "Ahilyanagar", "Aurangabad", "Bangalore",
    "Baner", "Bengaluru", "Bhopal", "Bombay", "Chakan", "Chandigarh",
    "Chennai", "Coimbatore", "Delhi", "Faridabad", "Ghaziabad", "Gurgaon",
    "Gurugram", "Guwahati", "Hyderabad", "Indore", "Jaipur", "Kanpur",
    "Khed", "Kochi", "Kolkata", "Lucknow", "Ludhiana", "Madras", "Mumbai",
    "Mysore", "Nagpur", "Nashik", "Navi Mumbai", "Noida", "Patna", "Pimpri",
    "Prabhadevi", "Pune", "Raigad", "Rajkot", "Shivajinagar", "Supa", "Surat",
    "Thane", "Trivandrum", "Vadodara", "Varanasi", "Vishakhapatnam",
)

_PATTERN = re.compile(
    r"(?<![A-Za-z])(?:" + "|".join(sorted(CITIES, key=len, reverse=True)) + r")(?![A-Za-z])",
    re.IGNORECASE,
)


@register
class CityRecognizer(RegexRecognizer):
    name = "city"
    label = "LOCATION"
    priority = 60
    pattern = _PATTERN
