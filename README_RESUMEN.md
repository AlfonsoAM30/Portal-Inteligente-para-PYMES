# 🧠 IApadrinado: Portal Inteligente para PYMES

## ¿Qué es?
IApadrinado es una plataforma integral para la gestión, análisis y diseño de productos orientada a pequeñas y medianas empresas (PYMES). Combina inteligencia artificial generativa, análisis de datos y automatización de flujos de trabajo para potenciar la competitividad de tu negocio.

## ¿Cómo se usa?
1. **Clona el repositorio y accede a la carpeta:**
   ```bash
   git clone https://github.com/tuusuario/IApadrinado.git
   cd IApadrinado
   ```
2. **Instala las dependencias:**
   - Recomendado: usa el entorno Docker (ver más abajo)
   - O bien, crea un entorno virtual Python 3.11+ y ejecuta:
     ```bash
     pip install -r requirements.txt
     ```
3. **Arranca los servicios:**
   - Con Docker:
     ```bash
     docker-compose up -d --build
     ```
   - Manual (desarrollo):
     - Backend: `uvicorn app.api.orchestrator_services:app --host 0.0.0.0 --port 8000 --reload`
     - Frontend: `python -m app.frontend.main_ui`
4. **Accede a la app:**
   - Navega a [http://localhost:8090](http://localhost:8090)

## Funcionalidades principales
- **Estudio de Diseño Asistido:** Sube una URL de producto y genera imágenes, descripciones y análisis de mercado automáticamente.
- **Gestión de Proyectos:** Guarda, carga y elimina proyectos de diseño en slots personales.
- **Análisis de Producto:** Extrae metadatos, reseñas y realiza análisis de sentimiento.
- **Orquestación Inteligente:** Flujos de trabajo gestionados por grafos de agentes (LangGraph).

## Frameworks y tecnologías usadas
- **Backend:** FastAPI, LangGraph, SQLAlchemy, PostgreSQL
- **Frontend:** NiceGUI (Vue.js + Python)
- **IA y PLN:** Ollama (Llama 3.1), Stable Diffusion, ControlNet, BERT, SpaCy, KeyBERT
- **Visión Artificial:** Segment Anything (SAM), CLIP, FAISS, OpenCV
- **Infraestructura:** Docker, Docker Compose, Playwright
- **Seguridad:** bcrypt, Fernet

## Estructura básica del proyecto
```
app/
  core/           # Logs y utilidades
  orchestration/  # Flujos LangGraph
  backend/        # Lógica de negocio y servicios
  frontend/       # Interfaz NiceGUI
  ...
data/             # Datos y salidas
models/           # Modelos IA
requirements/     # Requisitos por módulo
```

## Notas
- El sistema está preparado para funcionar tanto en local como en contenedores Docker.
- Los modelos de IA se descargan automáticamente al primer uso.
- Para producción, configura las variables de entorno y credenciales necesarias.

## Contacto
- Alfonso Armenta Martín: alfonsoarmentamartin@gmail.com
- Álvaro García Velasco: alvarogarciavelasco1212@gmail.com

---
Proyecto para la asignatura de Aplicaciones de la Inteligencia Artificial (URJC).
