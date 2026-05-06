import math
from copy import deepcopy

from bson import ObjectId
from flask import Flask, jsonify, render_template, request

import queries
from load_data import get_database, load_all_data

app = Flask(__name__)

QUERY_DEFINITIONS = {
    1: {
        "name": "Top Available Listings",
        "collection": "calendar",
        "pipeline": queries.query_1,
        "description": "Top 10 listings with the most available days.",
    },
    2: {
        "name": "December Records by City and Year",
        "collection": "calendar",
        "pipeline": queries.query_2,
        "description": "Count December records by city and year.",
    },
    3: {
        "name": "Neighborhood Review Distribution",
        "collection": "listings",
        "pipeline": queries.query_3,
        "description": "Neighborhoods ranked by total reviews.",
    },
    4: {
        "name": "Room Type Ratings by City",
        "collection": "listings",
        "pipeline": queries.query_4,
        "description": "Average review score by room type in each city.",
    },
    5: {
        "name": "Average Price by Neighborhood",
        "collection": "listings",
        "pipeline": queries.query_5,
        "description": "Most expensive neighborhoods by average listing price.",
    },
    6: {
        "name": "Availability Across Cities",
        "collection": "listings",
        "pipeline": queries.query_6,
        "description": "Average annual availability and totals per city.",
    },
}


def _collection_for_name(db, name):
    if name == "calendar":
        return db.calendar
    if name == "listings":
        return db.listings
    if name == "reviews":
        return db.reviews
    if name == "neighborhoods":
        return db.neighborhoods
    raise ValueError(f"Unknown collection: {name}")


def _sanitize_for_json(value):
    if isinstance(value, dict):
        return {key: _sanitize_for_json(val) for key, val in value.items()}
    if isinstance(value, list):
        return [_sanitize_for_json(item) for item in value]
    if isinstance(value, ObjectId):
        return str(value)
    if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
        return None
    return value


def _serialize_listing(doc):
    return {
        "id": doc.get("id"),
        "name": doc.get("name"),
        "city": doc.get("city"),
        "neighbourhood": doc.get("neighbourhood_cleansed"),
        "room_type": doc.get("room_type"),
        "price": doc.get("price"),
        "accommodates": doc.get("accommodates"),
        "bathrooms_text": doc.get("bathrooms_text"),
        "beds": doc.get("beds"),
        "minimum_nights": doc.get("minimum_nights"),
        "availability_365": doc.get("availability_365"),
        "review_scores_rating": doc.get("review_scores_rating"),
        "number_of_reviews": doc.get("number_of_reviews"),
        "host_name": doc.get("host_name"),
    }


@app.route("/")
def index():
    safe_queries = {
        qid: {
            "name": details["name"],
            "description": details["description"],
        }
        for qid, details in QUERY_DEFINITIONS.items()
    }
    return render_template("index.html", queries=safe_queries)


@app.post("/api/load-data")
def api_load_data():
    try:
        summary = load_all_data()
        return jsonify(_sanitize_for_json({"ok": True, "summary": summary}))
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 500


@app.get("/api/listings")
def list_listings():
    limit = min(max(int(request.args.get("limit", 24)), 1), 120)
    skip = max(int(request.args.get("skip", 0)), 0)
    city = request.args.get("city")

    try:
        db = get_database()
        criteria = {"name": {"$ne": None}}
        if city:
            criteria["city"] = city

        projection = {
            "_id": 0,
            "id": 1,
            "name": 1,
            "city": 1,
            "neighbourhood_cleansed": 1,
            "room_type": 1,
            "price": 1,
            "accommodates": 1,
            "bathrooms_text": 1,
            "beds": 1,
            "minimum_nights": 1,
            "availability_365": 1,
            "review_scores_rating": 1,
            "number_of_reviews": 1,
            "host_name": 1,
        }

        total = db.listings.count_documents(criteria)
        rows = (
            db.listings.find(criteria, projection)
            .sort([("number_of_reviews", -1), ("id", 1)])
            .skip(skip)
            .limit(limit)
        )
        listings = [_serialize_listing(doc) for doc in rows]
        return jsonify(
            _sanitize_for_json(
                {
                    "ok": True,
                    "total": total,
                    "skip": skip,
                    "limit": limit,
                    "rows": listings,
                }
            )
        )
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 500


@app.get("/api/listings/<listing_id>")
def listing_detail(listing_id):
    try:
        db = get_database()
        id_candidates = [listing_id]
        if listing_id.isdigit():
            id_candidates.append(int(listing_id))
        listing = db.listings.find_one(
            {"id": {"$in": id_candidates}},
            {
                "_id": 0,
                "id": 1,
                "name": 1,
                "description": 1,
                "city": 1,
                "neighbourhood_cleansed": 1,
                "room_type": 1,
                "price": 1,
                "accommodates": 1,
                "bathrooms_text": 1,
                "beds": 1,
                "minimum_nights": 1,
                "availability_365": 1,
                "review_scores_rating": 1,
                "number_of_reviews": 1,
                "host_name": 1,
                "amenities": 1,
            },
        )
        if not listing:
            return jsonify({"ok": False, "error": "Listing not found"}), 404

        reviews = list(
            db.reviews.find(
                {"listing_id": {"$in": id_candidates}},
                {"_id": 0, "date": 1, "reviewer_name": 1, "comments": 1},
            )
            .sort([("date", -1)])
            .limit(6)
        )

        return jsonify(
            _sanitize_for_json(
                {"ok": True, "listing": _serialize_listing(listing), "reviews": reviews}
            )
        )
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 500


@app.get("/api/reviews")
def list_reviews():
    limit = min(max(int(request.args.get("limit", 30)), 1), 200)
    try:
        db = get_database()
        rows = list(
            db.reviews.find(
                {},
                {
                    "_id": 0,
                    "listing_id": 1,
                    "city": 1,
                    "date": 1,
                    "reviewer_name": 1,
                    "comments": 1,
                },
            )
            .sort([("date", -1)])
            .limit(limit)
        )
        return jsonify(_sanitize_for_json({"ok": True, "rows": rows}))
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 500


@app.get("/api/collections")
def list_collections():
    try:
        db = get_database()
        pipeline = [
            {"$match": {"neighbourhood_cleansed": {"$ne": None}, "price": {"$ne": None}}},
            {
                "$addFields": {
                    "priceNumber": {
                        "$convert": {
                            "input": {
                                "$replaceAll": {
                                    "input": {"$substr": ["$price", 1, 20]},
                                    "find": ",",
                                    "replacement": "",
                                }
                            },
                            "to": "double",
                            "onError": None,
                            "onNull": None,
                        }
                    }
                }
            },
            {"$match": {"priceNumber": {"$ne": None}}},
            {
                "$group": {
                    "_id": {
                        "city": "$city",
                        "neighbourhood": "$neighbourhood_cleansed",
                    },
                    "avgPrice": {"$avg": "$priceNumber"},
                    "listingCount": {"$sum": 1},
                    "avgRating": {"$avg": "$review_scores_rating"},
                }
            },
            {"$sort": {"listingCount": -1}},
            {"$limit": 24},
            {
                "$project": {
                    "_id": 0,
                    "city": "$_id.city",
                    "neighbourhood": "$_id.neighbourhood",
                    "listingCount": 1,
                    "avgPrice": {"$round": ["$avgPrice", 2]},
                    "avgRating": {"$round": ["$avgRating", 2]},
                }
            },
        ]
        rows = list(db.listings.aggregate(pipeline, allowDiskUse=True))
        return jsonify(_sanitize_for_json({"ok": True, "rows": rows}))
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 500


@app.get("/api/query/<int:query_id>")
def run_query(query_id):
    details = QUERY_DEFINITIONS.get(query_id)
    if not details:
        return jsonify({"ok": False, "error": "Query not found"}), 404

    try:
        db = get_database()
        collection = _collection_for_name(db, details["collection"])
        pipeline = deepcopy(details["pipeline"])
        result = list(collection.aggregate(pipeline, allowDiskUse=True))
        return jsonify(
            _sanitize_for_json(
                {
                    "ok": True,
                    "query_id": query_id,
                    "name": details["name"],
                    "count": len(result),
                    "rows": result,
                    "pipeline": pipeline,
                }
            )
        )
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 500


if __name__ == "__main__":
    app.run(debug=True, port=5000)
