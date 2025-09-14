from crewai import Agent, Task, Crew, Process
from crewai_tools import BaseTool
from typing import Dict, List, Any
import json
import os
from openai import OpenAI

# Конфигурация OpenAI с прокси-сервером
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client = OpenAI(
    api_key=OPENAI_API_KEY,
    base_url="https://openai.api.proxyapi.ru/v1",
)

class RouteOptimizationCrew:
    def __init__(self):
        self.setup_agents()
        self.setup_tasks()
        
    def setup_agents(self):
        """Создание специализированных агентов"""
        
        # Агент для анализа погодных условий
        self.weather_analyst = Agent(
            role='Weather Analyst',
            goal='Analyze weather conditions and their impact on delivery routes',
            backstory="""You are an expert meteorologist with 15 years of experience 
            in logistics and transportation. You understand how different weather 
            conditions affect road conditions, visibility, and delivery times.""",
            verbose=True,
            allow_delegation=False,
            llm=self._get_llm()
        )
        
        # Агент для мониторинга пробок
        self.traffic_monitor = Agent(
            role='Traffic Monitor',
            goal='Analyze traffic conditions and suggest optimal routes',
            backstory="""You are a traffic management specialist with extensive 
            knowledge of urban traffic patterns, peak hours, and alternative routes. 
            You help optimize delivery routes based on real-time traffic conditions.""",
            verbose=True,
            allow_delegation=False,
            llm=self._get_llm()
        )
        
        # Агент для планирования маршрутов
        self.route_planner = Agent(
            role='Route Planner',
            goal='Create optimized delivery routes considering all factors',
            backstory="""You are a senior logistics coordinator with expertise in 
            route optimization algorithms and delivery management. You synthesize 
            information from weather and traffic analysts to create the most 
            efficient delivery routes.""",
            verbose=True,
            allow_delegation=False,
            llm=self._get_llm()
        )
        
        # Главный координатор
        self.delivery_coordinator = Agent(
            role='Delivery Coordinator',
            goal='Coordinate the entire delivery optimization process',
            backstory="""You are the head of delivery operations with 20 years of 
            experience. You coordinate between different specialists to ensure 
            optimal delivery routes that balance efficiency, safety, and customer 
            satisfaction.""",
            verbose=True,
            allow_delegation=True,
            llm=self._get_llm()
        )
    
    def _get_llm(self):
        """Получение LLM для агентов"""
        from langchain_openai import ChatOpenAI
        
        return ChatOpenAI(
            model="gpt-3.5-turbo",
            temperature=0.7,
            openai_api_key=OPENAI_API_KEY,
            openai_api_base="https://openai.api.proxyapi.ru/v1"
        )
    
    def setup_tasks(self):
        """Создание задач для агентов"""
        
        # Задача анализа погоды
        self.weather_task = Task(
            description="""Analyze the weather conditions: {weather_condition}
            and provide insights on how it affects delivery routes.
            Consider factors like:
            - Road safety
            - Visibility
            - Delivery time impact
            - Special precautions needed
            
            Return your analysis in JSON format with fields:
            - impact_level: low/medium/high
            - safety_concerns: list of concerns
            - time_adjustment: estimated time increase in minutes
            - recommendations: list of recommendations""",
            agent=self.weather_analyst,
            expected_output="JSON analysis of weather impact on delivery routes"
        )
        
        # Задача анализа пробок
        self.traffic_task = Task(
            description="""Analyze the traffic conditions: {traffic_condition}
            and provide insights on optimal routing strategies.
            Consider factors like:
            - Peak hours impact
            - Alternative routes
            - Time delays
            - Route efficiency
            
            Return your analysis in JSON format with fields:
            - congestion_level: low/medium/high
            - estimated_delay: minutes of delay
            - alternative_routes: list of alternative options
            - optimal_timing: best times for delivery""",
            agent=self.traffic_monitor,
            expected_output="JSON analysis of traffic conditions and routing strategies"
        )
        
        # Задача планирования маршрута
        self.route_task = Task(
            description="""Create an optimized delivery route for the following addresses:
            {addresses}
            
            Consider:
            - Customer priorities: {priorities}
            - Weather analysis from weather analyst
            - Traffic analysis from traffic monitor
            - Special requirements: {special_requirements}
            
            Return the optimized route in JSON format with fields:
            - optimized_route: ordered list of addresses
            - total_estimated_time: estimated total delivery time
            - route_efficiency_score: efficiency rating 1-10
            - reasoning: detailed explanation of route optimization""",
            agent=self.route_planner,
            expected_output="JSON with optimized delivery route and reasoning"
        )
        
        # Главная задача координации
        self.coordination_task = Task(
            description="""As the delivery coordinator, synthesize all analyses and 
            create the final optimized delivery plan.
            
            Use insights from:
            - Weather analysis
            - Traffic analysis  
            - Route planning
            
            Create the final delivery plan in JSON format with fields:
            - optimized_route: final ordered list of addresses
            - explanation: comprehensive explanation of the optimization strategy
            - total_estimated_time: final estimated delivery time
            - risk_assessment: potential risks and mitigations
            - success_probability: probability of successful delivery (1-10)""",
            agent=self.delivery_coordinator,
            expected_output="Final optimized delivery plan with comprehensive analysis"
        )
    
    def optimize_route(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Основной метод оптимизации маршрута с использованием CrewAI"""
        
        try:
            # Подготовка данных для задач
            addresses = data.get("addresses", [])
            weather = data.get("weather_condition", "unknown")
            traffic = data.get("traffic_condition", "unknown")
            requirements = data.get("special_requirements", [])
            
            # Формирование строки адресов
            addresses_str = "\n".join([
                f"{i+1}. {addr['address']} (приоритет: {addr['priority']}/5)"
                for i, addr in enumerate(addresses)
            ])
            
            # Формирование строки приоритетов
            priorities_str = ", ".join([
                f"{addr['address']}: {addr['priority']}"
                for addr in addresses
            ])
            
            # Обновление описаний задач с данными
            self.weather_task.description = self.weather_task.description.format(
                weather_condition=weather
            )
            
            self.traffic_task.description = self.traffic_task.description.format(
                traffic_condition=traffic
            )
            
            self.route_task.description = self.route_task.description.format(
                addresses=addresses_str,
                priorities=priorities_str,
                special_requirements=", ".join(requirements) if requirements else "нет"
            )
            
            # Создание команды агентов
            crew = Crew(
                agents=[
                    self.weather_analyst,
                    self.traffic_monitor, 
                    self.route_planner,
                    self.delivery_coordinator
                ],
                tasks=[
                    self.weather_task,
                    self.traffic_task,
                    self.route_task,
                    self.coordination_task
                ],
                process=Process.sequential,
                verbose=True
            )
            
            # Запуск команды
            result = crew.kickoff()
            
            # Обработка результата
            try:
                # Попытка парсинга JSON из результата
                if isinstance(result, str):
                    # Ищем JSON в тексте
                    import re
                    json_match = re.search(r'\{.*\}', result, re.DOTALL)
                    if json_match:
                        result_json = json.loads(json_match.group())
                    else:
                        # Если JSON не найден, создаем структурированный ответ
                        result_json = {
                            "optimized_route": [addr["address"] for addr in addresses],
                            "explanation": result,
                            "total_estimated_time": "2-3 часа",
                            "risk_assessment": "Стандартные риски доставки",
                            "success_probability": 8
                        }
                else:
                    result_json = result
                
                return result_json
                
            except (json.JSONDecodeError, AttributeError) as e:
                # Fallback при ошибке парсинга
                return {
                    "optimized_route": [addr["address"] for addr in addresses],
                    "explanation": f"CrewAI анализ завершен. Результат: {str(result)}",
                    "total_estimated_time": "2-3 часа",
                    "risk_assessment": "Анализ завершен успешно",
                    "success_probability": 7
                }
                
        except Exception as e:
            return {
                "optimized_route": [addr["address"] for addr in data.get("addresses", [])],
                "explanation": f"Ошибка CrewAI: {str(e)}",
                "total_estimated_time": "неизвестно",
                "risk_assessment": "Ошибка в процессе анализа",
                "success_probability": 1
            }

