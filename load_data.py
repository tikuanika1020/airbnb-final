import pandas as pd
from pymongo import MongoClient
import certifi

client = MongoClient(
    "mongodb+srv://tikuanikaz_db_user:anika123@cluster-hw3.tp8k8jz.mongodb.net/?appName=Cluster-hw3",
    tlsCAFile=certifi.where()
)

db = client["airbnb"]

# 🔥 CLEAR OLD DATA FIRST
db.listings.drop()
db.calendar.drop()
db.reviews.drop()
db.neighborhoods.drop()

cities = ["sd", "salem", "portland", "la"]

for city in cities:
    print(f"Loading {city}...")

    # LISTINGS (limit)
    listings = pd.read_csv(f"listings_{city}.csv", nrows=5000)
    listings["city"] = city
    db.listings.insert_many(listings.to_dict("records"))

    # NEIGHBORHOODS (small anyway)
    neighborhoods = pd.read_csv(f"neighbourhoods_{city}.csv")
    neighborhoods["city"] = city
    db.neighborhoods.insert_many(neighborhoods.to_dict("records"))

    # REVIEWS (reduce more)
    reviews = pd.read_csv(f"reviews_{city}.csv", nrows=20000)
    reviews["city"] = city
    db.reviews.insert_many(reviews.to_dict("records"))

    # CALENDAR (limit + filter)
    calendar = pd.read_csv(f"calendar_{city}.csv", nrows=30000)
    calendar["date"] = pd.to_datetime(calendar["date"])

    calendar = calendar[
        calendar["date"].dt.month.isin([12, 1])
    ]

    calendar["city"] = city
    db.calendar.insert_many(calendar.to_dict("records"))

print("DONE")