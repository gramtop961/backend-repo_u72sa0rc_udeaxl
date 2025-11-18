import os
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from bson import ObjectId

from database import db, create_document, get_documents
from schemas import TobaccoProduct, ProductUpdate, BulkProducts, Label, Store, PriceUpdate

app = FastAPI(title="TabaDigit ESL API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"name": "TabaDigit ESL API", "status": "ok"}


@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }

    try:
        if db is not None:
            response["database"] = "✅ Connected & Working"
            response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    return response


# Utility to convert ObjectId to str in results

def _serialize(doc):
    if not doc:
        return doc
    doc = dict(doc)
    if doc.get("_id"):
        doc["id"] = str(doc.pop("_id"))
    return doc


# Products endpoints
@app.post("/api/products", response_model=dict)
async def create_product(product: TobaccoProduct):
    product_id = create_document("tobaccoproduct", product)
    return {"id": product_id}


@app.post("/api/products/bulk", response_model=dict)
async def create_products_bulk(payload: BulkProducts):
    inserted = []
    for item in payload.items:
        inserted.append(create_document("tobaccoproduct", item))
    return {"inserted": inserted, "count": len(inserted)}


@app.get("/api/products", response_model=List[dict])
async def list_products(q: Optional[str] = None, limit: int = 100):
    filter_dict = {}
    if q:
        # basic text search on name or brand using regex
        filter_dict = {"$or": [
            {"name": {"$regex": q, "$options": "i"}},
            {"brand": {"$regex": q, "$options": "i"}},
            {"sku": {"$regex": q, "$options": "i"}}
        ]}
    docs = get_documents("tobaccoproduct", filter_dict, limit)
    return [_serialize(d) for d in docs]


@app.patch("/api/products/{product_id}", response_model=dict)
async def update_product(product_id: str, updates: ProductUpdate):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not available")
    try:
        updates_dict = {k: v for k, v in updates.model_dump(exclude_unset=True).items() if v is not None}
        if not updates_dict:
            return {"updated": 0}
        res = db["tobaccoproduct"].update_one({"_id": ObjectId(product_id)}, {"$set": updates_dict})
        return {"updated": res.modified_count}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.delete("/api/products/{product_id}", response_model=dict)
async def delete_product(product_id: str):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not available")
    res = db["tobaccoproduct"].delete_one({"_id": ObjectId(product_id)})
    return {"deleted": res.deleted_count}


# Labels endpoints
@app.post("/api/labels", response_model=dict)
async def create_label(label: Label):
    label_id = create_document("label", label)
    return {"id": label_id}


@app.get("/api/labels", response_model=List[dict])
async def list_labels(limit: int = 100):
    docs = get_documents("label", {}, limit)
    return [_serialize(d) for d in docs]


@app.patch("/api/labels/{label_id}", response_model=dict)
async def update_label(label_id: str, payload: dict):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not available")
    res = db["label"].update_one({"_id": ObjectId(label_id)}, {"$set": payload})
    return {"updated": res.modified_count}


# Price updates endpoints
@app.post("/api/price-updates", response_model=dict)
async def create_price_update(update: PriceUpdate):
    upd_id = create_document("priceupdate", update)
    # Also apply to product immediately if status is done
    if db and update.new_price is not None:
        db["tobaccoproduct"].update_one({"sku": update.product_sku}, {"$set": {"price": update.new_price}})
    return {"id": upd_id}


@app.get("/api/price-updates", response_model=List[dict])
async def list_price_updates(limit: int = 100):
    docs = get_documents("priceupdate", {}, limit)
    return [_serialize(d) for d in docs]


# Public schema endpoint (useful for admin viewers)
class SchemaInfo(BaseModel):
    collections: List[str]


@app.get("/schema", response_model=SchemaInfo)
async def get_schema():
    return SchemaInfo(collections=[
        "tobaccoproduct",
        "label",
        "priceupdate",
        "store",
    ])


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
