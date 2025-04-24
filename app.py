import time
import json
import os
import traceback
from datetime import datetime
import requests
from get_token import get_token

# Configuración
POLLING_INTERVAL = 1 * 60  # 1 minutos en segundos
RETRY_INTERVAL = 10  # 10 segundos en caso de error
DATA_FOLDER = "data"
DATA_FILE = os.path.join(DATA_FOLDER, "alerts_data.json")
API_URL = "https://portal.instant-on.hpe.com/api/sites"

# Asegurar que exista la carpeta de datos
if not os.path.exists(DATA_FOLDER):
    os.makedirs(DATA_FOLDER)


def get_alerts_summary():
    """
    Función adaptada del código original para obtener el resumen de alertas
    """
    from datetime import timezone, timedelta
    
    token = get_token()
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(API_URL, headers=headers)
    if response.status_code != 200:
        raise Exception(f"Error obteniendo sitios: {response.status_code}")

    sites = response.json().get("elements", [])
    alert_summary = []
    
    argentina_tz = timezone(timedelta(hours=-3))

    for site in sites:
        if site.get("health") != "problem":
            continue

        site_id = site["id"]
        topology_url = f"{API_URL}/{site_id}/graphTopology"
        topology_resp = requests.get(topology_url, headers=headers)
        devices_problem = []

        if topology_resp.status_code == 200:
            nodes = topology_resp.json().get("nodes", [])
            for node in nodes:
                device = node.get("device")
                if not device:
                    continue

                health_conds = device.get("healthConditions", [])
                for cond in health_conds:
                    if cond.get("severity") == "poor":
                        seconds_since_last = device.get('numberOfSecondsSinceLastCommunication')
                        now = datetime.now(argentina_tz)
                        if seconds_since_last:
                            last_communication = now - timedelta(seconds=seconds_since_last)
                            last_communication_str = last_communication.strftime("%d/%m/%Y %H:%M:%S")
                        else:
                            last_communication_str = "Desconocido"

                        device_details = {
                            "device_name": device['name'],
                            "severity": cond.get("severity"),
                            "condition": cond.get("condition"),
                            "model": device.get('model'),
                            "seconds_since_last_communication": seconds_since_last,
                            "last_communication_datetime": last_communication_str,
                            "operational_state": device.get('operationalState'),
                            "ip_address": device.get('ipAddress'),
                            "mac_address": device.get('id'),
                            "device_type": device.get('deviceType'),
                            "status": device.get('status')
                        }

                        devices_problem.append(device_details)

            alert_summary.append({
                "site_id": site_id,
                "site_name": site.get("name"),
                "devices_problem": devices_problem,
                "total_devices_problem": len(devices_problem),
                "total_devices": len([node for node in nodes if node.get("device")])
            })

    return alert_summary

def save_data_to_file(data):
    """
    Guarda los datos en un archivo JSON con timestamp
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    data_with_timestamp = {
        "timestamp": timestamp,
        "data": data
    }
    
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data_with_timestamp, f, indent=2, ensure_ascii=False)
    
    print(f"[{timestamp}] Datos guardados correctamente en {DATA_FILE}")

def main_loop():
    """
    Bucle principal que ejecuta la recolección de datos cada POLLING_INTERVAL
    """
    print(f"Iniciando el recolector de datos. Intervalo: {POLLING_INTERVAL} segundos")
    print(f"Los datos se guardarán en: {DATA_FILE}")
    
    while True:
        try:
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Recopilando datos...")
            alerts_data = get_alerts_summary()
            save_data_to_file(alerts_data)
            
            # Esperar hasta el próximo intervalo
            time.sleep(POLLING_INTERVAL)
            
        except Exception as e:
            error_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"[{error_time}] Error: {str(e)}")
            print(f"Reintentando en {RETRY_INTERVAL} segundos...")
            
            # Guardar el error en un archivo de log
            with open(os.path.join(DATA_FOLDER, "error_log.txt"), "a") as log:
                log.write(f"[{error_time}] Error: {str(e)}\n")
                log.write(traceback.format_exc())
                log.write("\n" + "-"*50 + "\n")
            
            # Esperar y reintentar
            time.sleep(RETRY_INTERVAL)

if __name__ == "__main__":
    main_loop()