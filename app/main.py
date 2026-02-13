from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from src.app.v1 import (
    auth,
    users,
    inventory,
    primary_sales,
    secondary_sales,
    tertiary_sales,
    geography,
    product,
    production
)
from src.app.core.config import settings
from src.app.v1 import partner

# Initialize the App
app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    description="Backend system for HOM Distribution - Factory to End Consumer"
)


# --- SECURITY CONFIGURATION (The Magic Part) ---
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )

    # Define the Security Scheme (OAuth2 with Password Flow)
    openapi_schema["components"]["securitySchemes"] = {
        "OAuth2PasswordBearer": {
            "type": "oauth2",
            "flows": {
                "password": {
                    "tokenUrl": "/api/v1/auth/login",  # This must match your login endpoint
                    "scopes": {}
                }
            }
        }
    }

    # Apply security globally to all endpoints
    # (You can remove this line if you want to apply it manually per router)
    openapi_schema["security"] = [{"OAuth2PasswordBearer": []}]

    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi

# --- MIDDLEWARE ---
origins = [
    "http://localhost",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- ROUTERS ---

# Auth & Identity
app.include_router(auth.router, prefix="/api/v1/auth", tags=["01. Authentication"])
app.include_router(users.router, prefix="/api/v1/users", tags=["02. User Management"])

# Masters (Geo & Products)
app.include_router(geography.router, prefix="/api/v1/geo", tags=["03. Geography"])
app.include_router(product.router, prefix="/api/v1/products", tags=["04. Product Master"])

# Supply Chain Operations
app.include_router(production.router, prefix="/api/v1/production", tags=["05. Factory Production"])
app.include_router(inventory.router, prefix="/api/v1/inventory", tags=["06. Stock Management"])

# Sales Flows
app.include_router(primary_sales.router, prefix="/api/v1/primary-orders", tags=["07. Primary Sales (Factory -> SS)"])
app.include_router(secondary_sales.router, prefix="/api/v1/secondary-sales",
                   tags=["08. Secondary Sales (DB -> Retailer)"])
app.include_router(tertiary_sales.router, prefix="/api/v1/tertiary-sales",
                   tags=["09. Tertiary Sales (Retailer -> Barber)"])

app.include_router(partner.router, prefix="/api/v1/partners", tags=["10. Partners"])


# --- HEALTH CHECK ---
@app.get("/", tags=["Health Check"])
def root():
    return {
        "status": "online",
        "message": f"Welcome to {settings.PROJECT_NAME}",
        "docs": "/docs"
    }


if __name__ == "__main__":
    import uvicorn

    # Note: 'reload=True' is great for dev, but turn it off in production!
    uvicorn.run("src.app.main:app", host="127.0.0.1", port=8000, reload=True)