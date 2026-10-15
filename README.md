
# 🎩 Proyecto: IApadrinado - Portal Inteligente para PYMES

![Status](https://img.shields.io/badge/Status-Funcional-success)
![Python](https://img.shields.io/badge/Python-3.11-blue)
![LangGraph](https://img.shields.io/badge/Orquestación-LangGraph-orange)
![NiceGUI](https://img.shields.io/badge/Framework-NiceGUI-00aaff)
![Docker](https://img.shields.io/badge/Despliegue-Docker-2496ed)


## 🚀 Instalación Rápida
1. Clona el repositorio:
	```bash
	git clone https://github.com/tuusuario/IApadrinado.git
	cd IApadrinado
	```
2. Asegúrate de tener [Docker](https://www.docker.com/) y [Docker Compose](https://docs.docker.com/compose/) instalados.
3. Ejecuta:
	```bash
	docker-compose up -d --build
	```
4. Accede a la app en [http://localhost:8090](http://localhost:8090)

---

## 📋 Descripción del Proyecto
**IApadrinado** es una plataforma integral de gestión y marketing automatizado diseñada para potenciar la competitividad de las pequeñas y medianas empresas (PYMES). El sistema unifica herramientas críticas de administración empresarial con una avanzada suite de diseño visual basada en Inteligencia Artificial generativa.

El núcleo del sistema es un **orquestador basado en grafos de agentes (LangGraph)**, que gestiona flujos de trabajo complejos de forma asíncrona, desde la autenticación segura hasta la síntesis de imágenes de producto mediante modelos de difusión.

### Componentes y Capacidades Principales
1. **Estudio de Diseño Asistido (AI Design Studio)**: Un pipeline que permite extraer productos de sitios como Amazon mediante *scraping* asíncrono (*Playwright*), aislarlos con segmentación precisa (*SAM*) y generar nuevos entornos visuales publicitarios.
2. **Agente de Gestión (Management Agent)**: Basado en **Llama 3.1:8b (Ollama)**, interpreta comandos en lenguaje natural para realizar consultas a la base de datos corporativa, listado de empleados o generar informes técnicos de seguridad.
3. **Análisis Inteligente de Producto**: Extracción automática de metadatos visuales (*CLIP + FAISS*) y análisis de sentimiento de reseñas (*BERT + SpaCy*) para identificar las fortalezas competitivas del catálogo.
4. **Generación Híbrida**: Capacidad de alternar entre generación vía API de alta fidelidad (*Google Nano-Banana*) e inferencia local privada (*Stable Diffusion + ControlNet Canny*) para garantizar autonomía y privacidad.

## 🛠️ Stack Tecnológico
- **Orquestación de Agentes**: `LangGraph`.
- **Modelos de Lenguaje (LLM)**: `Ollama` (Llama 3.1:8b).
- **Visión Artificial**: `Segment Anything (SAM)`, `CLIP`, `FAISS`, `OpenCV`.
- **IA Generativa**: `Stable Diffusion`, `ControlNet (Canny)`, `Google API`.
- **Procesamiento de Lenguaje (PLN)**: `BERT`, `SpaCy`, `KeyBERT`.
- **Interfaz de Usuario**: `NiceGUI` (FastAPI/Vue.js).
- **Gestión de Datos y Seguridad**: `PostgreSQL`, `bcrypt` (Hashing), `Fernet` (Cifrado simétrico).
- **Infraestructura**: `Docker`, `Docker Compose`, `Playwright`.

## 📂 Estructura del Repositorio
```
├── app/
│   ├── core/
│   │   └── logger.py                # Sistema centralizado de logs
│   ├── orchestration/
│   │   ├── graph.py                 # Definición del flujo LangGraph
│   │   ├── state.py                 # Gestión de estados del flujo
│   │   └── nodes/                   # Nodos funcionales (auth, design, management, etc.)
│   ├── backend/
│   │   ├── auth/                    # Lógica de autenticación
│   │   ├── cybersecurity/           # Módulos de ciberseguridad
│   │   ├── llm/                     # Configuración de modelos LLM
│   │   ├── product_analyzer/        # Extracción y análisis de productos
│   │   ├── product_design/          # Generación y optimización de prompts
│   │   └── services/                # Servicios auxiliares (scraper, etc.)
│   ├── pages/
│   │   ├── auth.py                  # Vista de Login/Registro
│   │   ├── dashboard.py             # Selector de funcionalidades
│   │   ├── design.py                # Estudio creativo asistido por IA
│   │   └── management.py            # Panel conversacional de gestión
│   ├── tools/                       # Herramientas y utilidades
│   ├── theme.py                     # Temas visuales
│   └── main.py                      # Punto de entrada de la app
├── data/
│   ├── content_labels.json          # Etiquetas de contenido
│   ├── style_labels.json            # Etiquetas de estilo
│   └── output/                      # Salidas generadas
├── logs/                            # Logs de ejecución
├── models/                          # Modelos y pesos descargados
├── docker-compose.yml               # Orquestación de contenedores y volúmenes
├── Dockerfile                       # Imagen base de la aplicación
├── requirements.txt                 # Dependencias del ecosistema Python
├── LICENSE                          # Licencia del proyecto
└── README.md                        # Documentación principal
```


## 🐳 Despliegue con Docker
El sistema está completamente contenedorizado para garantizar portabilidad y persistencia de datos.

1. **Requisitos previos:**
	- Docker y Docker Compose instalados.
	- Acceso a Ollama (local o remoto).
2. **Construcción e inicio:**
	```bash
	docker-compose up -d --build
	```
3. **Primera ejecución:**
	Descarga automática de modelos locales (SAM, CLIP, BERT) y almacenamiento en volúmenes persistentes.
4. **Acceso:**
	[http://localhost:8090](http://localhost:8090)


## 🔒 Características de Seguridad

- **Aislamiento Multi-empresa**: Cifrado con claves únicas por empresa, impidiendo el acceso cruzado a información sensible.
- **Inferencia Local**: Opción de ejecutar los modelos críticos en local para mantener la soberanía sobre los datos.
- **Persistencia Robusta**: Modelos e imágenes generadas se almacenan en volúmenes mapeados (`/app/data/output`, `/app/models`), sobreviviendo a reinicios del contenedor.


## 🤝 Contribución
¿Quieres contribuir? ¡Las pull requests son bienvenidas! Por favor, abre un issue para discutir cambios importantes antes de hacerlos.

## 📬 Contacto e Información
Proyecto desarrollado para la asignatura de Aplicaciones de la Inteligencia Artificial (Grado en IA - URJC).

- Alfonso Armenta Martín: alfonsoarmentamartin@gmail.com
- Álvaro García Velasco: alvarogarciavelasco1212@gmail.com || https://github.com/alvaroG-IA

## 📄 Licencia
Este proyecto está bajo la licencia MIT. Consulta el archivo [LICENSE](LICENSE) para más detalles.









