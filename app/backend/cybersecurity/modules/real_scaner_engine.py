import requests
import time
from datetime import datetime

from app.backend.cybersecurity.reporter import SecurityReporter


class RealBreachScanner:
    def __init__(self):
        self.api_url = "https://api.xposedornot.com/v1/check-email/"
        self.headers = {"User-Agent": "CiberSecurity-IA-Project-2026"}

        # Catálogo brechas
        self.breach_catalog = [
            {"name": "Deep Web Leak", "severity": "High"},
            {"name": "Phishing Campaign DB", "severity": "Critical"},
            {"name": "Social Media Exploit", "severity": "Medium"},
            {"name": "Third-party Provider Breach", "severity": "Low"},
        ]

    def obtener_info_catalogo(self, nombre_brecha):
        nombre_str = str(nombre_brecha[0]) if isinstance(nombre_brecha, list) else str(nombre_brecha)
        nombre_min = nombre_str.lower()

        reglas_mapeo = {
            "exploit": "Deep Web Leak",
            "demandscience": "Third-party Provider Breach",
            "payhere": "Third-party Provider Breach",
            "hacker": "Deep Web Leak",
            "leak": "Deep Web Leak",
            "phish": "Phishing Campaign DB",
            "social": "Social Media Exploit"
        }

        for clave, categoria_objetivo in reglas_mapeo.items():
            if clave in nombre_min:
                for item in self.breach_catalog:
                    if item["name"] == categoria_objetivo:
                        return {
                            "cat_name": categoria_objetivo,
                            "real_name": nombre_str,
                            "severity": item["severity"]
                        }

        return {
            "cat_name": "Uncategorized Breach",
            "real_name": nombre_str,
            "severity": "Medium"
        }

    def consultar_api_real(self, email):
        try:
            response = requests.get(self.api_url + email, headers=self.headers, timeout=10)
            if response.status_code == 200:
                return response.json().get("breaches", [])
            return []
        except Exception:
            return []

    def ejecutar_escaneo(self, dominio, lista_usuarios):
        print(f"\nESCANEO DE RIESGO PARA: {dominio}")
        print("=" * 65)

        hallazgos_para_ia = []

        for usuario in lista_usuarios:
            email = f"{usuario}@{dominio}"
            print(f"Analizando: {email}...", end="\r")

            brechas_externas = self.consultar_api_real(email)

            if brechas_externas:
                print(f"\nHALLAZGO: {email} detectado en {len(brechas_externas)} sitios.")

                for b_nombre in brechas_externas:
                    info = self.obtener_info_catalogo(b_nombre)

                    hallazgos_para_ia.append((
                        email,
                        f"{info['cat_name']} ({info['real_name']})",
                        info['severity'],
                        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    ))

                    print(f"    -> [{info['severity']}] {info['cat_name']} (Fuente: {info['real_name']})")

            time.sleep(0.5)

        print("\n" + "=" * 65)
        print(f"Escaneo completado. {len(hallazgos_para_ia)} incidentes.")
        return hallazgos_para_ia


def parse_stream(s):
    for chunk in s:
        print(chunk['message']['content'], end='', flush=True)


if __name__ == "__main__":
    scanner = RealBreachScanner()
    reportero = SecurityReporter("PROYECTO CIBER 2026")

    usuarios_prueba = ["admin", "test", "contact"]
    dominio_prueba = "gmail.com"

    # Realizar el escaneo
    resultados = scanner.ejecutar_escaneo(dominio_prueba, usuarios_prueba)

    # Generar el informe
    if resultados:
        print("\n\nGENERANDO ANÁLISIS")
        print("-" * 65 + "\n")

        stream_informe = reportero.generar_informe_brechas(resultados)

        if stream_informe:
            parse_stream(stream_informe)
        else:
            print("Error: No se pudo conectar con el modelo.")

        print("\n\n" + "-" * 65)
    else:
        print("\nNo se detectaron vulnerabilidades externas.")