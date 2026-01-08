import re
from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime
import os
from dotenv import load_dotenv
import requests


load_dotenv()

TRAVELPAYOUTS_TOKEN = os.getenv("TRAVELPAYOUTS_TOKEN")

app = Flask(__name__)
CORS(app)



@app.route("/health")
def health():
    return "ok"


@app.route("/search-flights", methods=["POST"])
def search_flights():
    data = request.get_json(force=True)

    if not data:
        return jsonify({"error": "Invalid request body"}), 400
    trip_type = data.get("tripType")
    origin = data.get("from")
    destination = data.get("to")
    depart_date = data.get("departDate")
    return_date = data.get("returnDate")
    passengers = data.get("passengers", {})
    adults = passengers.get("adults", 1)
    children = passengers.get("children", 0)
    infants = passengers.get("infants", 0)
    print("PAX:", adults, children, infants)


    # ===== Validations =====
    if origin == destination:
        return jsonify({"error": "مدينة المغادرة والوصول يجب أن تكون مختلفة"}), 400

    if depart_date:
        selected = datetime.strptime(depart_date, "%Y-%m-%d").date()
        if selected < datetime.today().date():
            return jsonify({"error": "لا يمكن اختيار تاريخ ذهاب سابق"}), 400

    if trip_type == "round":
        if not return_date:
            return jsonify({"error": "تاريخ العودة مطلوب"}), 400

        r_selected = datetime.strptime(return_date, "%Y-%m-%d").date()
        d_selected = datetime.strptime(depart_date, "%Y-%m-%d").date()

        if r_selected < d_selected:
            return jsonify({"error": "تاريخ العودة لا يمكن أن يكون قبل الذهاب"}), 400

    # ===== Mock Amadeus results (مكان API الحقيقي لاحقًا) =====
    outbound_flights = [
        {
            "airline": "فلاي أديل",
            "from": origin,
            "to": destination,
            "departTime": "09:10",
            "arriveTime": "11:15",
            "duration": "2س",
            "stops": 0,
            "price": 350
        },
        {
            "airline": "الخطوط السعودية",
            "from": origin,
            "to": destination,
            "departTime": "14:30",
            "arriveTime": "16:45",
            "duration": "2س 15د",
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
            "duration": "2س",
            "stops": 0,
            "price": 360
        },
        {
            "airline": "الخطوط السعودية",
            "from": destination,
            "to": origin,
            "departTime": "21:30",
            "arriveTime": "23:45",
            "duration": "2س 15د",
            "stops": 0,
            "price": 500
        }
    ]

    # ===== One Way =====
    if trip_type == "oneway":
        return jsonify({
            "type": "oneway",
            "flights": outbound_flights
        })

    # ===== Round Trip (دمج ذهاب + عودة) =====
    round_trips = []

    for out in outbound_flights:
        for inn in inbound_flights:
            round_trips.append({
                "round": True,
                "outbound": out,
                "inbound": inn,
                "price": out["price"] + inn["price"]
            })

    return jsonify({
        "type": "round",
        "flights": round_trips
    })

AIRPORTS = [
    {"city": "الرياض", "name": "King Khalid International Airport", "iata": "RUH"},
    {"city": "جدة", "name": "King Abdulaziz International Airport", "iata": "JED"},
    {"city": "الدمام", "name": "King Fahd International Airport", "iata": "DMM"},
    {"city": "المدينة", "name": "Prince Mohammad Airport", "iata": "MED"},
    {"city": "أبها", "name": "Abha Airport", "iata": "AHB"},
    {"city": "الطائف", "name": "Taif Airport", "iata": "TIF"},
]


@app.route("/locations")
def locations():
    q = request.args.get("q", "").strip()
    if len(q) < 2:
        return jsonify([])

    url = "https://autocomplete.travelpayouts.com/places2"

    params = {
        "term": q,
        "locale": "en"
    }

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Accept": "application/json"
    }

    try:
        res = requests.get(
            url,
            params=params,
            headers=headers,
            timeout=10
        )
    except Exception as e:
        print("Autocomplete error:", e)
        return jsonify([])

    if res.status_code != 200:
        print("Autocomplete status:", res.status_code)
        return jsonify([])

    data = res.json()

    results = []

    def slugify(text):
            return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")

    for item in data:
        if not item.get("code"):
            continue

        city = item.get("name")
        country = item.get("country_name")

        if not city or not country:
            continue

        slug = f"{slugify(city)}-{slugify(country)}"

        results.append({
            "city": city,
            "iata": item.get("code"),
            "slug": slug
        })


    return jsonify(results)



if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)



