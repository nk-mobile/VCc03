from flask import Flask, request, jsonify
from openai import OpenAI
import os
import json
from typing import List, Dict, Any
from crewai_agents import RouteOptimizationCrew

app = Flask(__name__)

# Конфигурация OpenAI с прокси-сервером
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client = OpenAI(
    api_key=OPENAI_API_KEY,
    base_url="https://openai.api.proxyapi.ru/v1",
)

class RouteOptimizerAgent:
    def __init__(self):
        self.system_prompt = """Ты выступаешь как модуль автономного агента для оптимизации маршрутов доставки в учебном проекте. 

На вход ты получаешь список заказов и локаций, а также упрощённые условия: пробки, погода, задержки на складах, приоритет клиентов. 

На выходе ты должен предложить оптимизированный маршрут — в виде упорядоченного списка адресов и краткого пояснения. 

Решай задачу так, будто это реальное время, но используй эвристики и логику рассуждений вместо точного математического расчёта.

Отвечай ТОЛЬКО в формате JSON:
{
    "optimized_route": ["адрес1", "адрес2", "адрес3"],
    "explanation": "краткое пояснение логики оптимизации",
    "total_estimated_time": "примерное время в часах"
}"""
        
        # Инициализация CrewAI команды
        self.crew_optimizer = RouteOptimizationCrew()

    def create_prompt(self, data: Dict[str, Any]) -> str:
        """Создает промпт для ChatGPT на основе входных данных"""
        
        addresses = data.get("addresses", [])
        weather = data.get("weather_condition")
        traffic = data.get("traffic_condition")
        delays = data.get("warehouse_delays", {})
        requirements = data.get("special_requirements", [])
        
        prompt = f"""
Задача оптимизации маршрута доставки:

АДРЕСА ДОСТАВКИ:
"""
        
        for i, addr in enumerate(addresses, 1):
            prompt += f"{i}. {addr['address']} (приоритет: {addr['priority']}/5)\n"
        
        prompt += "\nУСЛОВИЯ:\n"
        
        if weather:
            weather_desc = {
                "sunny": "солнечная погода",
                "rain": "дождь",
                "snow": "снег", 
                "fog": "туман"
            }
            prompt += f"- Погода: {weather_desc.get(weather, weather)}\n"
        
        if traffic:
            traffic_desc = {
                "light": "легкие пробки",
                "moderate": "умеренные пробки",
                "heavy": "сильные пробки"
            }
            prompt += f"- Пробки: {traffic_desc.get(traffic, traffic)}\n"
        
        if delays:
            prompt += "- Задержки на складах:\n"
            for warehouse, delay in delays.items():
                prompt += f"  * {warehouse}: +{delay} минут\n"
        
        if requirements:
            prompt += f"- Особые требования: {', '.join(requirements)}\n"
        
        prompt += """
Определи оптимальный порядок доставки, учитывая:
1. Приоритеты клиентов
2. Погодные условия
3. Пробки
4. Задержки на складах
5. Особые требования

Ответь в формате JSON с полями: optimized_route, explanation, total_estimated_time
"""
        
        return prompt

    def optimize_route_crewai(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Оптимизирует маршрут через CrewAI команду агентов"""
        try:
            return self.crew_optimizer.optimize_route(data)
        except Exception as e:
            return {
                "optimized_route": [addr["address"] for addr in data.get("addresses", [])],
                "explanation": f"Ошибка CrewAI: {str(e)}",
                "total_estimated_time": "неизвестно",
                "risk_assessment": "Ошибка в процессе анализа",
                "success_probability": 1
            }

    def optimize_route(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Оптимизирует маршрут через ChatGPT API (fallback метод)"""
        
        try:
            prompt = self.create_prompt(data)
            
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=500
            )
            
            result_text = response.choices[0].message.content.strip()
            
            # Попытка парсинга JSON ответа
            try:
                result = json.loads(result_text)
                return result
            except json.JSONDecodeError:
                # Если ответ не в JSON формате, создаем структурированный ответ
                return {
                    "optimized_route": [addr["address"] for addr in data.get("addresses", [])],
                    "explanation": result_text,
                    "total_estimated_time": "2-3 часа"
                }
                
        except Exception as e:
            return {
                "optimized_route": [addr["address"] for addr in data.get("addresses", [])],
                "explanation": f"Ошибка при обращении к ChatGPT: {str(e)}",
                "total_estimated_time": "неизвестно"
            }

# Инициализация агента
agent = RouteOptimizerAgent()

@app.route("/", methods=["GET"])
def health_check():
    return jsonify({"status": "agent running", "service": "route-optimizer-agent"})

@app.route("/optimize", methods=["POST"])
def optimize():
    """Основной endpoint для оптимизации маршрута"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "Отсутствуют данные"}), 400
        
        # Валидация обязательных полей
        if "addresses" not in data or not data["addresses"]:
            return jsonify({"error": "Необходим список адресов"}), 400
        
        # Оптимизация маршрута
        result = agent.optimize_route(data)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({"error": f"Внутренняя ошибка: {str(e)}"}), 500

@app.route("/test", methods=["GET"])
def test_endpoint():
    """Тестовый endpoint с примером данных (ChatGPT)"""
    test_data = {
        "addresses": [
            {"address": "ул. Ленина, 10, Москва", "priority": 3},
            {"address": "пр. Мира, 25, Москва", "priority": 5},
            {"address": "ул. Тверская, 15, Москва", "priority": 2}
        ],
        "weather_condition": "rain",
        "traffic_condition": "heavy",
        "warehouse_delays": {"warehouse_1": 15},
        "special_requirements": ["хрупкий груз"]
    }
    
    result = agent.optimize_route(test_data)
    return jsonify(result)

@app.route("/optimize-crewai", methods=["POST"])
def optimize_crewai():
    """Endpoint для оптимизации маршрута через CrewAI команду агентов"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "Отсутствуют данные"}), 400
        
        # Валидация обязательных полей
        if "addresses" not in data or not data["addresses"]:
            return jsonify({"error": "Необходим список адресов"}), 400
        
        # Оптимизация маршрута через CrewAI
        result = agent.optimize_route_crewai(data)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({"error": f"Внутренняя ошибка: {str(e)}"}), 500

@app.route("/test-crewai", methods=["GET"])
def test_crewai_endpoint():
    """Тестовый endpoint для CrewAI с примером данных"""
    test_data = {
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
    
    result = agent.optimize_route_crewai(test_data)
    return jsonify(result)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
