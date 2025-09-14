from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import httpx
import os

app = FastAPI(title="Delivery Route Optimizer API", version="1.0.0")

# Настройка CORS для работы с фронтендом
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Модели данных
class Address(BaseModel):
    address: str
    priority: int = 1  # 1-5, где 5 - высший приоритет

class DeliveryRequest(BaseModel):
    addresses: List[Address]
    weather_condition: Optional[str] = None  # "sunny", "rain", "snow", "fog"
    traffic_condition: Optional[str] = None  # "light", "moderate", "heavy"
    warehouse_delays: Optional[dict] = None  # {"warehouse_id": delay_minutes}
    special_requirements: Optional[List[str]] = None

class RouteResponse(BaseModel):
    optimized_route: List[str]
    explanation: str
    total_estimated_time: Optional[str] = None

# Конфигурация
AGENT_URL = os.getenv("AGENT_URL", "http://localhost:5000")

@app.get("/")
async def root():
    return {"message": "Delivery Route Optimizer API", "status": "running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.post("/optimize-route", response_model=RouteResponse)
async def optimize_route(request: DeliveryRequest):
    """
    Оптимизирует маршрут доставки на основе входных данных
    """
    try:
        # Валидация входных данных
        if not request.addresses:
            raise HTTPException(status_code=400, detail="Список адресов не может быть пустым")
        
        if len(request.addresses) < 2:
            raise HTTPException(status_code=400, detail="Необходимо минимум 2 адреса для оптимизации")
        
        # Подготовка данных для агента
        agent_data = {
            "addresses": [{"address": addr.address, "priority": addr.priority} for addr in request.addresses],
            "weather_condition": request.weather_condition,
            "traffic_condition": request.traffic_condition,
            "warehouse_delays": request.warehouse_delays,
            "special_requirements": request.special_requirements
        }
        
        # Отправка запроса агенту
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{AGENT_URL}/optimize",
                json=agent_data,
                timeout=30.0
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=500, 
                    detail=f"Ошибка агента: {response.text}"
                )
            
            result = response.json()
            
            return RouteResponse(
                optimized_route=result.get("optimized_route", []),
                explanation=result.get("explanation", ""),
                total_estimated_time=result.get("total_estimated_time")
            )
            
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Таймаут запроса к агенту")
    except httpx.ConnectError:
        raise HTTPException(status_code=503, detail="Агент недоступен")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Внутренняя ошибка сервера: {str(e)}")

@app.get("/example")
async def get_example():
    """
    Возвращает пример данных для тестирования
    """
    return {
        "example_request": {
            "addresses": [
                {"address": "ул. Ленина, 10, Москва", "priority": 3},
                {"address": "пр. Мира, 25, Москва", "priority": 5},
                {"address": "ул. Тверская, 15, Москва", "priority": 2}
            ],
            "weather_condition": "rain",
            "traffic_condition": "heavy",
            "warehouse_delays": {"warehouse_1": 15},
            "special_requirements": ["хрупкий груз", "срочная доставка"]
        }
    }

@app.post("/optimize-route-crewai", response_model=RouteResponse)
async def optimize_route_crewai(request: DeliveryRequest):
    """
    Оптимизирует маршрут доставки через CrewAI команду агентов
    """
    try:
        # Валидация входных данных
        if not request.addresses:
            raise HTTPException(status_code=400, detail="Список адресов не может быть пустым")
        
        if len(request.addresses) < 2:
            raise HTTPException(status_code=400, detail="Необходимо минимум 2 адреса для оптимизации")
        
        # Подготовка данных для агента
        agent_data = {
            "addresses": [{"address": addr.address, "priority": addr.priority} for addr in request.addresses],
            "weather_condition": request.weather_condition,
            "traffic_condition": request.traffic_condition,
            "warehouse_delays": request.warehouse_delays,
            "special_requirements": request.special_requirements
        }
        
        # Отправка запроса агенту CrewAI
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{AGENT_URL}/optimize-crewai",
                json=agent_data,
                timeout=60.0  # Увеличиваем таймаут для CrewAI
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=500, 
                    detail=f"Ошибка CrewAI агента: {response.text}"
                )
            
            result = response.json()
            
            return RouteResponse(
                optimized_route=result.get("optimized_route", []),
                explanation=result.get("explanation", ""),
                total_estimated_time=result.get("total_estimated_time")
            )
            
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Таймаут запроса к CrewAI агенту")
    except httpx.ConnectError:
        raise HTTPException(status_code=503, detail="CrewAI агент недоступен")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Внутренняя ошибка сервера: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
