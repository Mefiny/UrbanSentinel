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
