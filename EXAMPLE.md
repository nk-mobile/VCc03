# Пример использования системы оптимизации маршрутов

## Быстрый старт

### 1. Настройка окружения

```bash
# Скопируйте файл с переменными окружения
cp .env.example .env

# Отредактируйте .env файл и добавьте ваш OpenAI API ключ
echo "OPENAI_API_KEY=your_actual_api_key_here" > .env
```

### 2. Запуск системы

```bash
# Сборка и запуск всех сервисов
docker-compose up --build

# Или в фоновом режиме
docker-compose up --build -d
```

### 3. Доступ к приложению

- **Frontend**: http://localhost:8080
- **Backend API**: http://localhost:8000
- **Agent**: http://localhost:5000

## Пример использования

### Сценарий: Доставка в дождливую погоду

**Входные данные:**
- Адреса:
  1. ул. Ленина, 10, Москва (приоритет 3)
  2. пр. Мира, 25, Москва (приоритет 5) 
  3. ул. Тверская, 15, Москва (приоритет 2)
- Погода: Дождь
- Пробки: Сильные
- Особые требования: хрупкий груз, срочная доставка

**Ожидаемый результат:**
ИИ-агент проанализирует условия и предложит оптимальный порядок доставки, учитывая:
- Приоритеты клиентов
- Погодные условия (дождь может влиять на дороги)
- Пробки (сильные пробки требуют обхода)
- Особые требования (хрупкий груз требует осторожности)

**Пример ответа:**
```json
{
  "optimized_route": [
    "пр. Мира, 25, Москва",
    "ул. Ленина, 10, Москва", 
    "ул. Тверская, 15, Москва"
  ],
  "explanation": "Начинаем с адреса высшего приоритета (пр. Мира, 25). Из-за дождя и сильных пробок выбираем маршрут, минимизирующий время в пробках. Хрупкий груз доставляем в первую очередь.",
  "total_estimated_time": "2.5-3 часа"
}
```

## API Endpoints

### Backend API (FastAPI)

#### POST /optimize-route
Оптимизирует маршрут доставки

**Запрос:**
```json
{
  "addresses": [
    {"address": "ул. Ленина, 10, Москва", "priority": 3},
    {"address": "пр. Мира, 25, Москва", "priority": 5},
    {"address": "ул. Тверская, 15, Москва", "priority": 2}
  ],
  "weather_condition": "rain",
  "traffic_condition": "heavy",
  "special_requirements": ["хрупкий груз", "срочная доставка"]
}
```

**Ответ:**
```json
{
  "optimized_route": ["пр. Мира, 25, Москва", "ул. Ленина, 10, Москва", "ул. Тверская, 15, Москва"],
  "explanation": "Объяснение логики оптимизации...",
  "total_estimated_time": "2.5-3 часа"
}
```

#### GET /example
Возвращает пример данных для тестирования

### Agent API (Flask)

#### POST /optimize
Основной endpoint агента для оптимизации

#### GET /test
Тестовый endpoint с примером данных

## Тестирование

### Тест через curl

```bash
# Тест backend API
curl -X POST "http://localhost:8000/optimize-route" \
  -H "Content-Type: application/json" \
  -d '{
    "addresses": [
      {"address": "ул. Ленина, 10, Москва", "priority": 3},
      {"address": "пр. Мира, 25, Москва", "priority": 5}
    ],
    "weather_condition": "rain",
    "traffic_condition": "heavy"
  }'

# Тест agent напрямую
curl -X GET "http://localhost:5000/test"
```

### Тест через веб-интерфейс

1. Откройте http://localhost:8080
2. Нажмите "Загрузить пример" для заполнения тестовых данных
3. Нажмите "Оптимизировать маршрут"
4. Просмотрите результат

## Структура проекта

```
├── frontend/              # HTML/JS интерфейс
│   ├── index.html        # Главная страница
│   └── Dockerfile        # Docker конфигурация
├── backend/               # FastAPI сервер
│   ├── main.py           # Основной код API
│   ├── requirements.txt  # Python зависимости
│   └── Dockerfile        # Docker конфигурация
├── agent/                 # Python агент
│   ├── main.py           # Код агента
│   ├── requirements.txt  # Python зависимости
│   └── Dockerfile        # Docker конфигурация
├── docker-compose.yml     # Конфигурация всех сервисов
├── .env.example          # Пример переменных окружения
└── README.md             # Документация
```

## Логи и отладка

```bash
# Просмотр логов всех сервисов
docker-compose logs

# Просмотр логов конкретного сервиса
docker-compose logs backend
docker-compose logs agent
docker-compose logs frontend

# Перезапуск сервиса
docker-compose restart backend
```

## Остановка системы

```bash
# Остановка всех сервисов
docker-compose down

# Остановка с удалением volumes
docker-compose down -v
```
