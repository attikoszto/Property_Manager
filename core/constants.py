BERCHTESGADEN_LAT = 47.6301
BERCHTESGADEN_LNG = 13.0044
DEFAULT_RADIUS_KM = 5.0

PLATFORMS = ["airbnb", "booking"]

AMENITY_FEATURES = [
    "wifi",
    "parking",
    "sauna",
    "pool",
    "balcony",
    "kitchen",
    "washer",
]

SEASONALITY_FACTORS = {
    1: 1.4,
    2: 1.4,
    3: 0.9,
    4: 0.9,
    5: 1.1,
    6: 1.1,
    7: 1.5,
    8: 1.5,
    9: 1.0,
    10: 1.0,
    11: 0.7,
    12: 1.6,
}

WEEKDAY_FACTORS = {
    0: 0.9,   # Monday
    1: 0.9,   # Tuesday
    2: 0.9,   # Wednesday
    3: 0.95,  # Thursday
    4: 1.1,   # Friday
    5: 1.2,   # Saturday
    6: 1.1,   # Sunday
}

SIMILARITY_TOP_K = 20

PRICE_MULTIPLIER_OPTIONS = [0.9, 1.0, 1.1, 1.2]

# Weighted competitor set: external listings dominate the signal
EXTERNAL_LISTING_WEIGHT = 1.0
SYSTEM_LISTING_WEIGHT = 0.3

CLEANING_TASK_STATUSES = ["pending", "assigned", "confirmed", "in_progress", "completed"]

NOTIFICATION_CHANNELS = ["sms", "email", "push", "whatsapp"]

DAYS_TO_CHECKIN_ADJUSTMENTS = {
    60: 1.15,
    30: 1.05,
    14: 1.0,
    7: 0.95,
    3: 0.90,
    1: 0.85,
}
