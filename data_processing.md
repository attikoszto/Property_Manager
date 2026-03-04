# Data Processing Architecture – Classes and DataFrames

## Purpose

Define a clean architecture for data processing and business logic in the AI Property Manager system.

The goal is to maintain a clear separation between:

- domain models
- business services
- data processing
- machine learning models

The system should avoid monolithic scripts built entirely around DataFrames and instead use structured classes combined with efficient data processing tools.

---

# Architectural Principle

The recommended architecture combines:

Domain Classes  
+  
DataFrames for analytical computations

Classes handle structure and business logic.  
DataFrames handle large-scale data transformations and calculations.

---

# Why Not Pure Pandas Scripts

Many data science projects rely entirely on Pandas scripts.

Example structure:

pricing_script.py  
analysis_script.py  
data_script.py  

This approach leads to problems:

- poor modularity
- hard to maintain
- business logic mixed with data processing
- difficult testing
- difficult scaling

For production systems this architecture becomes fragile.

---

# Role of Classes

Classes should represent the core domain objects and services of the system.

Examples of domain entities:

Listing  
Booking  
Cleaner  
Event  

Example Listing model:

```python
class Listing:

    def __init__(self, id, capacity, bedrooms, size, rating):
        self.id = id
        self.capacity = capacity
        self.bedrooms = bedrooms
        self.size = size
        self.rating = rating