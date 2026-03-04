# Competitive Set Rules – Excluding System Customers

## Purpose

To prevent pricing distortion and algorithmic convergence, listings that use the system must not influence the pricing calculations of other listings using the same system.

This ensures that pricing decisions are based on real market data rather than internally generated prices.

---

# Core Principle

Listings that are customers of the system must be excluded from the competitive set used for pricing calculations.

This prevents the system from referencing its own pricing decisions.

---

# Database Requirement

The listings table must include a field indicating whether a listing belongs to a system customer.

Example schema:

listings

id  
external_id  
platform  
lat  
lng  
capacity  
bedrooms  
bathrooms  
square_meters  
rating  
review_count  
amenities  
base_price  
owner_id  
is_customer  

Field description:

is_customer = true → listing belongs to a system user  
is_customer = false → listing is an external competitor

---

# Competitive Set Construction

The competitive set must only include comparable listings that are not customers of the system.

Basic query logic:

SELECT *
FROM listings
WHERE distance < search_radius
AND is_customer = false

Example search radius:

5 km

---

# Excluding Listings From The Same Owner

If a property owner manages multiple listings, these listings must not compete with each other.

Filter rule:

owner_id != current_owner_id

Example logic:

SELECT *
FROM listings
WHERE distance < search_radius
AND is_customer = false
AND owner_id != current_owner_id

---

# Similarity Filtering

After filtering by ownership and system membership, the system should identify similar listings.

Similarity dimensions:

capacity  
bedrooms  
bathrooms  
square_meters  
rating  
review_count  
amenities  
distance_to_center  

Nearest neighbor search should then determine the most comparable listings.

Typical configuration:

top 20 most similar listings

---

# Weighted Competitor Sets (Advanced)

If the system gains high market penetration in a region, excluding all customer listings may reduce available market data.

In this case, customer listings can optionally be included with reduced weight.

Example weighting:

external_listings_weight = 1.0  
system_listings_weight = 0.3  

External listings should always dominate the competitive signal.

---

# Pricing Dependency

The competitive set is used to calculate market reference metrics such as:

median_price  
price_distribution  
occupancy_rate  

These values feed into the pricing engine.

Example:

final_price =  
base_price  
* demand_index  
* competition_adjustment  

competition_adjustment is based on the median price of the competitive set.

---

# Reinforcement Learning Separation

Reinforcement learning must rely only on internal booking data.

Training signals:

own listing prices  
own booking conversions  
time-to-booking  
own occupancy rates  

External competitor data should not influence the reinforcement learning reward function.

---

# Summary

To ensure accurate market pricing:

1. Listings that use the system must be excluded from competitor analysis.  
2. Listings owned by the same owner must be excluded.  
3. Similar listings are selected using nearest neighbor search.  
4. External listings should dominate the competitive signal.  
5. Reinforcement learning must rely only on internal booking outcomes.

This design prevents the pricing system from influencing itself and preserves realistic market signals.