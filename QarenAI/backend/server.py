import re
import time
import hashlib
import os
from datetime import datetime

import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

# ================== CONFIG ==================
FLIGHT_CACHE = {}
FLIGHT_CACHE_TTL = 15 * 60       # 15 دقيقة

LOCATIONS_CACHE = {}
LOCATIONS_CACHE_TTL = 60 * 60 * 24  # 24 ساعة

load_dotenv()

app = Flask(__name__)
CORS(app)

# ================== HELPERS ==================
def build_flight_cache_key(payload):
    key = (
        f"{payload.get('from')}-"
        f"{payload.get('to')}-"
        f"{payload.get('departDate')}-"
        f"{payload.get('returnDate')}-"
        f"{payload.get('tripType')}-"
        f"A{payload['passengers'].get('adults',1)}"
        f"C{payload['passengers'].get('children',0)}"
        f"I{payload['passengers'].get('infants',0)}"
    )
    return hashlib.md5(key.encode()).hexdigest()


def slugify(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")

# ================== ROUTES ==================
@app.route("/health")
def health():
    return "ok"


@app.route("/search-flights", methods=["POST"])
def search_flights():
    payload = request.get_json(force=True)

    if not payload:
        return jsonify({"error": "Invalid request body"}), 400

    cache_key = build_flight_cache_key(payload)
    now = time.time()

    cached = FLIGHT_CACHE.get(cache_key)
    if cached and now - cached["time"] < FLIGHT_CACHE_TTL:
        print("⚡ served from cache")
        return jsonify(cached["data"])

    # -------- Parse payload --------
    trip_type = payload.get("tripType")
    origin = payload.get("from")
    destination = payload.get("to")
    depart_date = payload.get("departDate")
    return_date = payload.get("returnDate")
    passengers = payload.get("passengers", {})

    adults = passengers.get("adults", 1)
    children = passengers.get("children", 0)
    infants = passengers.get("infants", 0)

    # -------- Validations --------
    if origin == destination:
        return jsonify({"error": "مدينة المغادرة والوصول يجب أن تكون مختلفة"}), 400

    if depart_date:
        d_selected = datetime.strptime(depart_date, "%Y-%m-%d").date()
        if d_selected < datetime.today().date():
            return jsonify({"error": "لا يمكن اختيار تاريخ ذهاب سابق"}), 400

    if trip_type == "round":
        if not return_date:
            return jsonify({"error": "تاريخ العودة مطلوب"}), 400

        r_selected = datetime.strptime(return_date, "%Y-%m-%d").date()
        if r_selected < d_selected:
            return jsonify({"error": "تاريخ العودة لا يمكن أن يكون قبل الذهاب"}), 400

    # -------- Mock Amadeus (مؤقت) --------
    outbound_flights = [
        {
            "airline": "فلاي أديل",
            "from": origin,
            "to": destination,
            "departTime": "09:10",
            "arriveTime": "11:15",
            "duration": "PT2H",
            "stops": 0,
            "price": 350
        },
        {
            "airline": "الخطوط السعودية",
            "from": origin,
            "to": destination,
            "departTime": "14:30",
            "arriveTime": "16:45",
            "duration": "PT2H15M",
            "stops": 0,
            "price": 520
        }
    ]

    inbound_flights = [
        {
            "airline": "فلاي أديل",
            "from": destination,
            "to": origin,
            "departTime": "18:00",
            "arriveTime": "20:05",
            "duration": "PT2H",
            "stops": 0,
            "price": 360
        },
        {
            "airline": "الخطوط السعودية",
            "from": destination,
            "to": origin,
            "departTime": "21:30",
            "arriveTime": "23:45",
            "duration": "PT2H15M",
            "stops": 0,
            "price": 500
        }
    ]

    # -------- One Way --------
    if trip_type == "oneway":
        response_data = {
            "type": "oneway",
            "flights": outbound_flights
        }

        FLIGHT_CACHE[cache_key] = {
            "time": time.time(),
            "data": response_data
        }

        return jsonify(response_data)

    # -------- Round Trip --------
    round_trips = []
    for out in outbound_flights:
        for inn in inbound_flights:
            round_trips.append({
                "round": True,
                "outbound": out,
                "inbound": inn,
                "price": out["price"] + inn["price"]
            })

    response_data = {
        "type": "round",
        "flights": round_trips
    }

    FLIGHT_CACHE[cache_key] = {
        "time": time.time(),
        "data": response_data
    }

    return jsonify(response_data)


@app.route("/locations")
def locations():
    q = request.args.get("q", "").strip().lower()
    if len(q) < 2:
        return jsonify([])

    cache_key = f"loc:{q}"
    now = time.time()

    cached = LOCATIONS_CACHE.get(cache_key)
    if cached and now < cached["expires"]:
        return jsonify(cached["data"])

    url = "https://autocomplete.travelpayouts.com/places2"
    params = {"term": q, "locale": "en"}

    try:
        res = requests.get(url, params=params, timeout=10)
    except Exception as e:
        print("Autocomplete error:", e)
        return jsonify([])

    if res.status_code != 200:
        return jsonify([])

    data = res.json()
    results = []

    for item in data:
        if not item.get("code"):
            continue

        city = item.get("name")
        country = item.get("country_name")
        if not city or not country:
            continue

        results.append({
            "city": city,
            "iata": item.get("code"),
            "slug": f"{slugify(city)}-{slugify(country)}"
        })

    LOCATIONS_CACHE[cache_key] = {
        "data": results,
        "expires": now + LOCATIONS_CACHE_TTL
    }

    return jsonify(results)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)




