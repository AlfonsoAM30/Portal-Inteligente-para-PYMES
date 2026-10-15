import random
from dotenv import load_dotenv
from datetime import datetime

from app.backend.db.session import db_session

class BreachSimulator:
    def __init__(self):

        load_dotenv()

        self.breach_catalog = [
            {"name": "Deep Web Leak", "severity": "High", "weight": 0.10},
            {"name": "Phishing Campaign DB", "severity": "Critical", "weight": 0.20},
            {"name": "Social Media Exploit", "severity": "Medium", "weight": 0.30},
            {"name": "Third-party Provider Breach", "severity": "Low", "weight": 0.40},
        ]

        self.individual_attack_probability = 0.15 

    def simulate_scan_results(self, empresa_id):
        try:
            with db_session(empresa_id) as cur:

                cur.execute("SELECT nombre_usuario FROM empleados WHERE empresa_id = %s", (empresa_id,))
                users = [row[0] for row in cur.fetchall()]

                cur.execute("SELECT dominio FROM empresas WHERE id = %s", (empresa_id,))
                dominio = cur.fetchone()[0]
                
                if not users or not dominio:
                    print(f"⚠️ Datos insuficientes para empresa {empresa_id}")
                    return 

                hallazgos_totales = 0
                print(f"🔍 Iniciando escaneo exhaustivo para {dominio}...")
                for user in users:
                    email = f"{user}{dominio}"
                    
                    if random.random() < self.individual_attack_probability:
                        
                        names = [b["name"] for b in self.breach_catalog]
                        weights = [b["weight"] for b in self.breach_catalog]
                        
                        ataque_elegido_name = random.choices(names, weights=weights, k=1)[0]
                        ataque_info = [b for b in self.breach_catalog if b["name"] == ataque_elegido_name][0]

                        cur.execute("""
                            INSERT INTO brechas (empresa_id, email_afectado, tipo_brecha, riesgo, fecha)
                            VALUES (%s, %s, %s, %s, %s)
                        """, (empresa_id, email, ataque_info["name"], ataque_info["severity"], datetime.now()))
                        
                        print(f"  [!] Hallazgo: {email} -> {ataque_info['name']}")
                        hallazgos_totales += 1

                print(f"✅ Escaneo finalizado. Total incidentes hoy: {hallazgos_totales}")

        except Exception as e:
            print(f"❌ Error en la simulación: {e}")

if __name__ == '__main__':
    empresa_id = 1
    simulator = BreachSimulator()
    simulator.simulate_scan_results(empresa_id)