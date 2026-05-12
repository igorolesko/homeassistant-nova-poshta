"""Constants for the Nova Poshta integration."""

DOMAIN = "nova_poshta"
API_KEY = "api_key"
PHONE = "phone"
TRACKING_NUMBERS = "tracking_numbers"

HTTP_TIMEOUT = 10
UPDATE_INTERVAL = 300  # 5 хвилин

# Статуси посилок Nova Poshta
# Джерело: реальні дані з getStatusDocuments API
TRACKING_STATUSES = {
    "1":  "Нова накладна",
    "2":  "Видалено",
    "3":  "Номер не знайдено",
    "4":  "Відправлено",
    "5":  "В дорозі",
    "6":  "У місті призначення",
    "7":  "Прибуло у відділення",
    "8":  "Прибуло у поштомат",
    "9":  "Отримано",
    "10": "Відмова від отримання",
    "11": "Повернення",
    "12": "Проблемне відправлення",
}

# Групи статусів для сенсорів
STATUSES_IN_TRANSIT = ("4", "5", "6")       # Їде до вас
STATUSES_ARRIVED = ("7", "8")               # Чекає у відділенні
STATUSES_DELIVERED = ("9",)                 # Отримано (забрали)
STATUSES_PROBLEM = ("10", "11", "12")       # Потребує уваги
