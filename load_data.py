import os
from pathlib import Path

import certifi
import pandas as pd
from pymongo import MongoClient

MONGO_URI = os.getenv(
    "MONGO_URI",
    "mongodb://localhost:27017",
)


def get_database():
    client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
    return client["airbnb"]


def _insert_dataframe(collection, df):
    records = df.where(pd.notnull(df), None).to_dict("records")
    if records:
        collection.insert_many(records)
    return len(records)


def load_all_data(base_dir=None):
    base_path = Path(base_dir) if base_dir else Path(__file__).resolve().parent
    parent_path = base_path.parent / "cs498_airbnb"
    search_paths = [base_path, parent_path]

    listings_limit = int(os.getenv("LISTINGS_LIMIT", "5000"))
    reviews_limit = int(os.getenv("REVIEWS_LIMIT", "15000"))
    calendar_limit = int(os.getenv("CALENDAR_LIMIT", "30000"))

    cities = ["sd", "salem", "portland", "la"]
    summary = {
        "listings": 0,
        "calendar": 0,
        "reviews": 0,
        "neighborhoods": 0,
    }

    resolved = {}
    for city in cities:
        for kind in ["listings", "reviews", "calendar", "neighbourhoods"]:
            filename = f"{kind}_{city}.csv"
            found = None
            for candidate in search_paths:
                path = candidate / filename
                if path.exists():
                    found = path
                    break
            if not found:
                raise FileNotFoundError(
                    f"Could not find {filename} in any of: {', '.join(str(p) for p in search_paths)}"
                )
            resolved[(city, kind)] = found

    db = get_database()
    staging_names = {
        "listings": "listings_staging",
        "calendar": "calendar_staging",
        "reviews": "reviews_staging",
        "neighborhoods": "neighborhoods_staging",
    }

    for stage_name in staging_names.values():
        db[stage_name].drop()

    try:
        for city in cities:
            listings = pd.read_csv(resolved[(city, "listings")], nrows=listings_limit)
            listings["city"] = city
            summary["listings"] += _insert_dataframe(db[staging_names["listings"]], listings)

            neighborhoods = pd.read_csv(resolved[(city, "neighbourhoods")])
            neighborhoods["city"] = city
            summary["neighborhoods"] += _insert_dataframe(
                db[staging_names["neighborhoods"]], neighborhoods
            )

            reviews = pd.read_csv(resolved[(city, "reviews")], nrows=reviews_limit)
            reviews["city"] = city
            summary["reviews"] += _insert_dataframe(db[staging_names["reviews"]], reviews)

            calendar = pd.read_csv(resolved[(city, "calendar")], nrows=calendar_limit)
            calendar["date"] = pd.to_datetime(calendar["date"], errors="coerce")
            calendar = calendar[calendar["date"].dt.month.isin([12, 1])]
            # Keep date as YYYY-MM-DD string so existing query pipelines work.
            calendar["date"] = calendar["date"].dt.strftime("%Y-%m-%d")
            calendar["city"] = city
            summary["calendar"] += _insert_dataframe(db[staging_names["calendar"]], calendar)

        for target_name, stage_name in staging_names.items():
            db[target_name].drop()
            db[stage_name].rename(target_name)
    except Exception:
        for stage_name in staging_names.values():
            db[stage_name].drop()
        raise

    return summary


if __name__ == "__main__":
    result = load_all_data()
    print("DONE")
    print(result)
