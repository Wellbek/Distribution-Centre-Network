"""Teaching defaults (brief §2.6) and run settings; edit values here, no CLI flags."""
import os

SEED = 437

# Company and instance
FULL_STORES = 10_000
MIN_STORES, MAX_STORES = 500, 1400          # per DC at full scale
DC_FIXED = 150e6                            # KRW/month, national mean
VEHICLE_MONTH = 5.5e6                       # KRW/month, driver included
FUEL_KM = 350.0                             # KRW/km
SPOT_DAY = 550e3                            # KRW/day
LATE_PEN = 120e3                            # delivery after 14:00
STOCKOUT_PEN = 500e3                        # no delivery
DAYS_MONTH = 365 / 12

# Vehicle day
CAP = 48                                    # roll cages
MAX_STOPS = 25
MAX_KM = 250.0
STOP_H = 15 / 60
SPEED = 35.0                                # km/h
DEPART = 4.0                                # 04:00
DEADLINE = 12.0                             # hard window
FAIL_AT = 14.0                              # after this a delivery is a failure
SHIFT_END = 13.0                            # 10 h shift from 03:00 incl. 1 h loading
BREAK_H = 0.5                               # legal break inside the shift (30 min per 4 h)

# Departure-wave check: hourly waves inside the 04:00-07:00 window, 1 h loading per dock; docks sized so a DC at the
# store cap (brief: beyond 1,400 stores docks cannot cope) dispatches today's vehicles per store in these waves
WAVES = (4.0, 5.0, 6.0, 7.0)

# Parallel territories (results do not depend on it)
WORKERS = min(os.cpu_count() or 1, 16)

# Fleet policy: newsvendor fractile = 1 - owned cost per day / spot rate = 0.671
FLEET_Q = 1 - VEHICLE_MONTH / DAYS_MONTH / SPOT_DAY

# Distances: placeholder until the OSRM cache exists
DETOUR = 1.30
DETOUR_MOUNTAIN = 1.45                      # Gangwon, North Gyeongsang

# Demand days and search
SEARCH_DAYS, FINAL_DAYS, HELDOUT_DAYS = 7, 28, 14
BUDGET = 40

# Far stores: a route beyond 250 km or the shift needs a second driver (relay) [ASSUMPTION]
RELAY_DAY = VEHICLE_MONTH / (365 / 12)      # one extra driver-day, priced like an owned vehicle-day
RELAY_SWEEP = (0.0, RELAY_DAY, 550e3)       # reversal row: free, driver-day, spot rate
REACH_KM, FAR_KM = 55.0, 125.0              # noon reach of a full route; 250 km round trip
DEMO_PROFILE = "full"                    # only this profile rebuilds ../demo.html

# Run profiles: fraction of stores kept (fixed cost and bounds scale with it)
REDUCED = dict(name="reduced", fraction=0.2, pool_per_k=14)
FULL = dict(name="full", fraction=1.0, pool_per_k=30)
