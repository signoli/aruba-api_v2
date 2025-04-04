from flask import Flask, jsonify, request
from get_token import get_token
import requests

app = Flask(__name__)

API_URL = "https://portal.instant-on.hpe.com/api/sites"
GLOBAL_ALERTS_URL = "https://portal.instant-on.hpe.com/api/globalAlerts"

def fetch_site_data(site_id, endpoint):
    token = get_token()
    headers = {"Authorization": f"Bearer {token}"}
    url = f"{API_URL}/{site_id}/{endpoint}"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    return {"error": "Unauthorized or site not found"}, response.status_code

def get_sites():
    token = get_token()
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(API_URL, headers=headers)
    if response.status_code == 200:
        data = response.json()
        filtered_sites = [
            {
                "id": site["id"],
                "name": site["name"],
                "configuredLocation": site["configuredLocation"],
                "dashboard": f"/dashboard/{site['id']}",
                "deviceStacks": f"/deviceStacks/{site['id']}",
                "capabilities": f"/capabilities/{site['id']}",
                "inventory": f"/inventory/{site['id']}",
                "graphTopology": f"/graphTopology/{site['id']}",
                "details": f"/sites/{site['id']}",
                "alerts": f"/alerts/{site['id']}"
            }
            for site in data.get("elements", []) if site.get("health") == "problem"
        ]
        return filtered_sites
    return []

def get_global_alerts():
    token = get_token()
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(GLOBAL_ALERTS_URL, headers=headers)
    if response.status_code == 200:
        return response.json()
    return {"error": "Unauthorized or failed to fetch global alerts"}, response.status_code

@app.route("/sites", methods=["GET"])
def sites():
    return jsonify(get_sites())

@app.route("/sites/<site_id>", methods=["GET"])
def site_details(site_id):
    return jsonify(fetch_site_data(site_id, ""))

@app.route("/dashboard/<site_id>", methods=["GET"])
def dashboard(site_id):
    return jsonify(fetch_site_data(site_id, "dashboard"))

@app.route("/deviceStacks/<site_id>", methods=["GET"])
def device_stacks(site_id):
    return jsonify(fetch_site_data(site_id, "deviceStacks"))

@app.route("/capabilities/<site_id>", methods=["GET"])
def capabilities(site_id):
    return jsonify(fetch_site_data(site_id, "capabilities"))

@app.route("/inventory/<site_id>", methods=["GET"])
def inventory(site_id):
    return jsonify(fetch_site_data(site_id, "inventory"))

@app.route("/graphTopology/<site_id>", methods=["GET"])
def graph_topology(site_id):
    return jsonify(fetch_site_data(site_id, "graphTopology"))

@app.route("/alerts/<site_id>", methods=["GET"])
def alerts(site_id):
    return jsonify(fetch_site_data(site_id, "alerts"))

@app.route("/globalAlerts", methods=["GET"])
def global_alerts():
    return jsonify(get_global_alerts())

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
