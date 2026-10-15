from fastapi import APIRouter, HTTPException, FastAPI
from app.backend.services.scraper import scrape_product

app = FastAPI(title="Management Service")
router = APIRouter(prefix="/api/scraper", tags=["Scraper"])

@router.get("/product")
async def get_product(url: str):
    try:
        result = await scrape_product(url)

        if not result:
            raise HTTPException(
                status_code=404,
                detail="No se pudo scrapear el producto"
            )

        return result

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error en scraper: {str(e)}"
        )

app.include_router(router)