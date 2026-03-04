# Advanced Demand Signals and Differentiation Features

## Purpose

This document defines advanced demand signals and predictive features that extend beyond traditional short-term rental pricing tools.

Most existing tools rely primarily on:

- seasonality
- competitor prices
- basic occupancy signals

The goal of this system is to build a predictive demand engine that incorporates micro-factors and forward-looking signals.

---

# 1. Weather Forecast Feature Pipeline

The system must use weather forecasts for future stay dates rather than relying only on current weather.

Weather data must be mapped to each potential stay date.

Example:

stay_date = 15 January  
weather_features = forecast_for_15_january

### Required features

snowfall_next_3_days  
snowfall_next_7_days  
temperature_forecast  
temperature_trend  
sun_hours_forecast  
cloud_cover_forecast  
rain_probability  
wind_speed  

### Pipeline

weather_api  
↓  
forecast ingestion  
↓  
weather_features_table  
↓  
feature generation per stay date

---

# 2. Ski Condition Index

For winter tourism destinations, the system should calculate a ski condition score.

This score represents the quality of skiing conditions and predicts demand spikes.

Example formula:

ski_condition_index =  
snow_depth  
× fresh_snow_factor  
× sun_factor  
× temperature_factor  
× wind_factor  

Interpretation:

high ski_condition_index → strong ski tourism demand.

---

# 3. Sun After Snow Signal

A common booking trigger in ski regions is new snow followed by sunshine.

Feature logic:

sun_after_snow =  

snowfall_last_48h > threshold  
AND  
sun_hours_next_24h > threshold  

If true:

demand_spike_probability increases.

---

# 4. Outdoor Condition Index (Summer Tourism)

For summer destinations the system should measure outdoor activity conditions.

Example formula:

outdoor_index =  

temperature_comfort_score  
× sun_hours  
× inverse_rain_probability  
× wind_factor  

Interpretation:

warm + sunny + low rain probability → tourism demand increases.

---

# 5. Demand Momentum Signals

Demand trends can indicate accelerating or declining market conditions.

The system should compute trend features such as:

occupancy_trend_3_days  
occupancy_trend_7_days  
booking_velocity_trend  
market_price_trend  

If demand momentum increases:

pricing engine may increase prices more aggressively.

---

# 6. Booking Window Prediction

The system should predict how many days before check-in a booking is likely to occur.

Example model output:

expected_booking_lead_time

### Features

season  
property_type  
location  
price  
day_of_week  
holiday_calendar  

This allows better price adjustments based on booking window behavior.

---

# 7. Demand Shock Detection

Sudden demand spikes can occur due to events or external factors.

Possible signals:

event announcements  
transport disruptions  
weather changes  
festival schedules  

Indicators:

sudden occupancy jump  
rapid competitor price increase  

If detected:

demand_shock = true

Pricing engine may react by increasing prices more aggressively.

---

# 8. Search Demand Signals

Search interest can indicate future demand.

Possible data sources:

Google Trends

Example query:

"berchtesgaden skiurlaub"

Feature examples:

search_interest_index  
search_interest_trend  

If search interest increases:

future tourism demand may increase.

---

# 9. Flight Price Signals

For international tourism destinations, flight prices affect travel demand.

Possible features:

average_flight_price  
flight_price_trend  
flight_availability  

If flights become cheaper:

tourism demand increases.

---

# 10. Shadow Price Testing

Even without direct booking data, the system can estimate demand elasticity.

Example logic:

system_price = 180  
market_price = 150  

Monitor:

how quickly competitor listings at 150 are booked.

This helps approximate price elasticity of the market.

---

# 11. Market Saturation Detection

Supply levels influence pricing power.

Feature example:

available_listings_ratio

Formula example:

available_listings_ratio =  
available_listings / total_listings

Interpretation:

high ratio → oversupply → lower pricing power.

---

# 12. Booking Probability Model

A predictive model should estimate booking probability.

Example function:

predict_booking_probability(date, listing_features)

Possible model types:

XGBoost  
LightGBM  

### Example input features

weather_forecast  
season  
events  
snow_index  
micro_location_score  
days_to_checkin  
market_occupancy  

### Model output

booking_probability

---

# Strategic Differentiation

The most unique components of the system should include:

1. Weather forecast features tied to future stay dates  
2. Ski and outdoor condition indices  
3. Demand momentum signals  

These features create a predictive pricing system rather than a reactive one.

---

# Long Term Advantage

The long-term competitive advantage will come from continuously learning demand curves.

price → booking_probability

Using this relationship the system can optimize revenue using the formula:

revenue = price × booking_probability



# Market Data Pipeline – Scraping, Booking Detection and Revenue Signals

## Purpose

The system must collect large-scale market data from short-term rental platforms in order to build advanced pricing and demand prediction models.

This pipeline provides the following capabilities:

- full market data collection across Germany
- competitor pricing analysis
- availability tracking
- booking detection
- booking probability estimation
- reinforcement learning signals for pricing models

The scraping system runs automatically three times per day.

---

# GitHub Workflow (Scraping 3 Times per Day)

File location:

.github/workflows/scrape_airbnb.yml

Example workflow:

```yaml
name: scrape-airbnb-data

on:
  schedule:
    - cron: "0 3 * * *"
    - cron: "0 11 * * *"
    - cron: "0 19 * * *"

  workflow_dispatch:

jobs:
  scrape:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Run listing scraper
        env:
          DATABASE_URL: ${{ secrets.DATABASE_URL }}
        run: python scripts/scrape_listings.py

      - name: Run availability scraper
        env:
          DATABASE_URL: ${{ secrets.DATABASE_URL }}
        run: python scripts/scrape_availability.py

      - name: Run price scraper
        env:
          DATABASE_URL: ${{ secrets.DATABASE_URL }}
        run: python scripts/scrape_prices.py