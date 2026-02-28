RISK_CATEGORIES = ["Crime", "Traffic", "Fraud", "Infrastructure Failure"]

# Priority scoring weights
W_RISK = 0.4
W_ECONOMIC = 0.3
W_CREDIBILITY = 0.2
W_RECENCY = 0.1

# Source credibility mapping
SOURCE_CREDIBILITY = {
    "government": 1.0,
    "news": 0.85,
    "citizen_report": 0.7,
    "social_media": 0.5,
}

# District coordinates (simulated urban layout)
DISTRICT_COORDS = {
    "District A": (31.2304, 121.4737),
    "District B": (31.2390, 121.4990),
    "District C": (31.2120, 121.4580),
    "District D": (31.2500, 121.4400),
    "District E": (31.2200, 121.5100),
}

# GNews API configuration
GNEWS_API_KEY = "015b1149112b44328b521e8f91406505"
GNEWS_BASE_URL = "https://gnews.io/api/v4"
