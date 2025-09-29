from flask import jsonify, request
from datetime import datetime
import os
import json
from models import ShipAIS
from config import URLS
from utils import safe_float

def register_routes(app):
    @app.route('/api/ais/latest', methods=['GET'])
    def get_latest_data():
        results = {}
        for url in URLS:
            key = url.replace('https://www.marinetraffic.com/getData/', '').replace('/', '_').replace(':', '_')
            latest = ShipAIS.query.filter_by(source=key).order_by(ShipAIS.timestamp.desc()).first()
            if latest:
                results[key] = latest.to_dict()
        return jsonify({
            "timestamp": datetime.utcnow().isoformat(),
            "results": results
        })

    @app.route('/api/ais/history', methods=['GET'])
    def get_ship_history():
        try:
            query = ShipAIS.query

            if request.args.get("shipname"):
                query = query.filter(ShipAIS.shipname.ilike(f"%{request.args['shipname']}%"))
            if request.args.get("ship_id"):
                query = query.filter_by(ship_id=request.args["ship_id"])
            if request.args.get("start") and request.args.get("end"):
                start = datetime.fromisoformat(request.args.get("start"))
                end = datetime.fromisoformat(request.args.get("end"))
                query = query.filter(ShipAIS.timestamp.between(start, end))

            if (request.args.get("min_lat") and request.args.get("max_lat") and
                request.args.get("min_lon") and request.args.get("max_lon")):
                min_lat = safe_float(request.args.get("min_lat"))
                max_lat = safe_float(request.args.get("max_lat"))
                min_lon = safe_float(request.args.get("min_lon"))
                max_lon = safe_float(request.args.get("max_lon"))
                query = query.filter(
                    ShipAIS.lat.between(min_lat, max_lat),
                    ShipAIS.lon.between(min_lon, max_lon)
                )

            results = [r.to_dict() for r in query.order_by(ShipAIS.timestamp.desc())]
            return jsonify(results)
        except Exception as e:
            return jsonify({"error": str(e)}), 400

    @app.route('/api/save_alarm_area', methods=['POST'])
    def save_alarm_area():
        """
        接收 GeoJSON（FeatureCollection 或任意 JSON），並寫入 static/alarm_area.geojson
        前端會 POST 完整 GeoJSON 物件
        """
        try:
            geojson = request.get_json()
            if not geojson:
                return jsonify({"error": "no JSON body"}), 400
            static_path = os.path.join(app.static_folder, 'alarm_area.geojson')
            with open(static_path, 'w', encoding='utf-8') as f:
                json.dump(geojson, f, ensure_ascii=False, indent=2)
            return jsonify({"status": "ok"}), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route('/')
    def show_map():
        return app.send_static_file('ships_map.html')