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

# Weather-based demand signal thresholds
SNOWFALL_48H_THRESHOLD = 5.0      # cm for sun-after-snow trigger
SUN_HOURS_THRESHOLD = 4.0         # hours for sun-after-snow trigger
SKI_INDEX_HIGH_DEMAND = 7.0       # ski index above this → demand spike
OUTDOOR_INDEX_HIGH_DEMAND = 7.0   # outdoor index above this → demand spike

# Demand shock detection
DEMAND_SHOCK_THRESHOLD = 0.15     # occupancy change > 15% = shock

# Search demand queries for the region
SEARCH_QUERIES = [
    "berchtesgaden skiurlaub",
    "berchtesgaden ferienwohnung",
    "königssee urlaub",
    "berchtesgaden wandern",
]

# Scraping schedule: 3 times per day (03:00, 11:00, 19:00 UTC)
SCRAPE_CRON_SCHEDULES = ["0 3 * * *", "0 11 * * *", "0 19 * * *"]
