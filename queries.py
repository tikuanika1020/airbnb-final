# Airbnb MongoDB Aggregation Queries

query_1 = [
    {
        '$match': {
            'available': 't'
        }
    }, {
        '$group': {
            '_id': '$listing_id', 
            'available_days': {
                '$sum': 1
            }
        }
    }, {
        '$sort': {
            'available_days': -1
        }
    }, {
        '$limit': 10
    }, {
        '$lookup': {
            'from': 'listings', 
            'localField': '_id', 
            'foreignField': 'id', 
            'as': 'listing'
        }
    }, {
        '$unwind': '$listing'
    }, {
        '$project': {
            'listing_name': '$listing.name', 
            'available_days': 1, 
            'price': '$listing.price', 
            'city': '$listing.city'
        }
    }
]


query_2 = [
    {
        '$addFields': {
            'date_converted': {
                '$dateFromString': {
                    'dateString': '$date'
                }
            }
        }
    }, {
        '$addFields': {
            'year': {
                '$year': '$date_converted'
            }
        }
    }, {
        '$match': {
            '$expr': {
                '$eq': [
                    {
                        '$month': '$date_converted'
                    }, 12
                ]
            }
        }
    }, {
        '$lookup': {
            'from': 'listings', 
            'localField': 'listing_id', 
            'foreignField': 'id', 
            'as': 'listing'
        }
    }, {
        '$unwind': '$listing'
    }, {
        '$group': {
            '_id': {
                'city': '$listing.city', 
                'year': '$year'
            }, 
            'total_reviews': {
                '$sum': 1
            }
        }
    }, {
        '$project': {
            '_id': 0, 
            'city': '$_id.city', 
            'year': '$_id.year', 
            'total_reviews': 1
        }
    }, {
        '$sort': {
            '_id.year': 1
        }
    }
]

query_3 = [
    {
        '$match': {
            'neighbourhood_cleansed': {
                '$ne': None
            }
        }
    }, {
        '$group': {
            '_id': '$neighbourhood_cleansed', 
            'totalReviews': {
                '$sum': '$number_of_reviews'
            }, 
            'listingCount': {
                '$sum': 1
            }, 
            'avgReviewsPerListing': {
                '$avg': '$number_of_reviews'
            }
        }
    }, {
        '$sort': {
            'totalReviews': -1
        }
    }, {
        '$project': {
            '_id': 0, 
            'neighbourhood': '$_id', 
            'totalReviews': 1, 
            'listingCount': 1, 
            'avgReviewsPerListing': {
                '$round': [
                    '$avgReviewsPerListing', 2
                ]
            }
        }
    }
]

query_4 = [
    {
        '$match': {
            '$expr': {
                '$eq': [
                    '$review_scores_rating', '$review_scores_rating'
                ]
            }, 
            'city': {
                '$ne': None
            }, 
            'room_type': {
                '$ne': None
            }
        }
    }, {
        '$group': {
            '_id': {
                'city': '$city', 
                'room_type': '$room_type'
            }, 
            'avgRating': {
                '$avg': '$review_scores_rating'
            }, 
            'listingCount': {
                '$sum': 1
            }
        }
    }, {
        '$sort': {
            '_id.city': 1, 
            'avgRating': -1
        }
    }, {
        '$project': {
            '_id': 0, 
            'city': '$_id.city', 
            'room_type': '$_id.room_type', 
            'avgRating': {
                '$round': [
                    '$avgRating', 2
                ]
            }, 
            'listingCount': 1
        }
    }
]

query_5 = [
    {
        '$match': {
            'price': {
                '$ne': None
            }, 
            'neighbourhood_cleansed': {
                '$ne': None
            }, 
            'city': {
                '$ne': None
            }
        }
    }, {
        '$addFields': {
            'priceNumber': {
                '$convert': {
                    'input': {
                        '$replaceAll': {
                            'input': {
                                '$substr': [
                                    '$price', 1, 20
                                ]
                            }, 
                            'find': ',', 
                            'replacement': ''
                        }
                    }, 
                    'to': 'double', 
                    'onError': None, 
                    'onNull': None
                }
            }
        }
    }, {
        '$match': {
            'priceNumber': {
                '$ne': None
            }
        }
    }, {
        '$group': {
            '_id': {
                'city': '$city', 
                'neighbourhood': '$neighbourhood_cleansed'
            }, 
            'avgPrice': {
                '$avg': '$priceNumber'
            }, 
            'listingCount': {
                '$sum': 1
            }
        }
    }, {
        '$sort': {
            'avgPrice': -1
        }
    }, {
        '$project': {
            '_id': 0, 
            'city': '$_id.city', 
            'neighbourhood': '$_id.neighbourhood', 
            'avgPrice': {
                '$round': [
                    '$avgPrice', 2
                ]
            }, 
            'listingCount': 1
        }
    }
]

query_6 = [
    {
        '$match': {
            'city': {
                '$ne': None
            }, 
            'availability_365': {
                '$type': 'number'
            }
        }
    }, {
        '$group': {
            '_id': '$city', 
            'avgAvailability365': {
                '$avg': '$availability_365'
            }, 
            'totalAvailableDays': {
                '$sum': '$availability_365'
            }, 
            'listingCount': {
                '$sum': 1
            }
        }
    }, {
        '$sort': {
            'avgAvailability365': -1
        }
    }, {
        '$project': {
            '_id': 0, 
            'city': '$_id', 
            'avgAvailability365': {
                '$round': [
                    '$avgAvailability365', 2
                ]
            }, 
            'totalAvailableDays': 1, 
            'listingCount': 1
        }
    }
]