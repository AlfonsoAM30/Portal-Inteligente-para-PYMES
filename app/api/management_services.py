import json
from fastapi import FastAPI, HTTPException, APIRouter, status
from typing import List, Optional
from pydantic import BaseModel, EmailStr

from app.backend.db.session import db_session
from app.backend.services.management import load_employes, view_company_data, view_personal_data, security_report
from app.backend.auth.auth_logic import login_user, register_company

app = FastAPI(title="Management Service")
router = APIRouter(prefix="/api/management", tags=["Management"])

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    apodo: str
    nombre_real: str
    nombre_empresa: str
    dominio: str
    telefono_oficial: str


@router.post("/auth/login")
def login(request: LoginRequest):
    result = login_user(request.email, request.password)

    if "error" in result:
        raise HTTPException(status_code=401, detail=result['error'])

    token = f"user_token_{result['user_id']}"
    
    return {
        "access_token": token,
        "user": result
    }

@router.post("/auth/register")
def register(request: RegisterRequest):
    result = register_company(request.model_dump())

    if "error" in result:
        raise HTTPException(status_code=400, detail=result['error'])

    return {"status": "success", "message": "Empresa y administrador registrados correctamente"}

@router.get("/employees/{empresa_id}")
def get_employees(empresa_id: int):
    try:
        rows = load_employes(empresa_id)

        if not rows:
            return []
        
        return [
            {
                "id": r[0],
                "alias": r[1],
                "puesto": r[2],
                "nombre": r[3],
                "tel": r[4],
            }
            for r in rows
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al cargar empleados: {str(e)}")
        

@router.get("/company/{empresa_id}")
def get_company(empresa_id: int):
    try:
        row = view_company_data(empresa_id)
        if not row:
            raise HTTPException(status_code=404, detail="Empresa no encontrada")
        
        return {
            "id": row[0],
            "nombre": row[1],
            "dominio": row[2],
            "tel": row[3],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error de base de datos al buscar empresa: {str(e)}")


@router.get("/profile/{empresa_id}")
def get_profile(empresa_id: int):
    try:
        rows = view_personal_data(empresa_id)
        if not rows:
            return []
            
        return [
            {
                "id": r[0],
                "email": r[1],
                "apodo": r[2],
                "rol": r[3],
                "iban": r[4],
                "fecha": r[5],
            }
            for r in rows
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al cargar perfil personal: {str(e)}")

@router.get("/breaches/{empresa_id}")
def get_breaches(empresa_id: int):
    try:
        reporte = security_report(empresa_id)
        if not reporte:
            return {"reporte": [], "mensaje": "No se encontraron brechas de seguridad para esta empresa."}
        return {"reporte": reporte}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al generar reporte de ciberseguridad: {str(e)}")


class ChatSavePayload(BaseModel):
    thread_id: str
    empresa_id: int
    slot: int
    titulo: str
    product_image_url: str
    product_description: Optional[str] = None
    product_reviews: List[str] = [] 

class ChatResponse(BaseModel):
    thread_id: str
    slot: int
    titulo: str
    product_image_url: str
    product_description: Optional[str] = None
    product_reviews: List[str] = []


@router.get("/chats/{empresa_id}", response_model=List[ChatResponse])
async def get_empresa_chats(empresa_id: int):
    with db_session(empresa_id) as cur:
        cur.execute("""
            SELECT thread_id, slot, titulo, product_image_url, product_description, product_reviews
            FROM chats 
            WHERE empresa_id = %s 
            ORDER BY slot ASC
        """, (empresa_id,))
        
        rows = cur.fetchall()
        
        chats = []
        for row in rows:
            raw_reviews = row[5]
            if isinstance(raw_reviews, str):
                reviews_list = json.loads(raw_reviews)
            elif isinstance(raw_reviews, list):
                reviews_list = raw_reviews
            else:
                reviews_list = []

            chats.append({
                "thread_id": row[0],
                "slot": row[1],
                "titulo": row[2],
                "product_image_url": row[3],
                "product_description": row[4], 
                "product_reviews": reviews_list 
            })
            
        return chats


@router.post("/chats/save")
async def save_empresa_chat(payload: ChatSavePayload):
    with db_session(payload.empresa_id) as cur:
        reviews_json = json.dumps(payload.product_reviews)

        cur.execute("""
            INSERT INTO chats (
                thread_id, empresa_id, slot, titulo, product_image_url, 
                product_description, product_reviews
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (empresa_id, slot) 
            DO UPDATE SET 
                thread_id = EXCLUDED.thread_id,
                titulo = EXCLUDED.titulo,
                product_image_url = EXCLUDED.product_image_url,
                product_description = EXCLUDED.product_description, -- Nuevo campo
                product_reviews = EXCLUDED.product_reviews,         -- Nuevo campo
                actualizado_en = CURRENT_TIMESTAMP
        """, (
            payload.thread_id, 
            payload.empresa_id, 
            payload.slot, 
            payload.titulo, 
            payload.product_image_url,
            payload.product_description, 
            reviews_json               
        ))
        return {"status": "success", "message": f"Slot {payload.slot} guardado/actualizado con metadatos estáticos."}
    
    
app.include_router(router)
