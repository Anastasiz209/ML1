import csv
import cianparser
import os
import time
import random
import requests
import logging

# Настройка логов
logging.basicConfig(filename='parsing_errors.log', level=logging.ERROR,
                    format='%(asctime)s:%(levelname)s:%(message)s')

def read_existing_data(file_name):
    if not os.path.isfile(file_name):
        return set()

    existing_urls = set()
    with open(file_name, 'r', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            existing_urls.add(row['url'])

    return existing_urls

def save_data_to_csv(data, file_name, mode='a'):
    if not data:
        return

    fieldnames = data[0].keys()
    file_exists = os.path.isfile(file_name)

    with open(file_name, mode, newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        if not file_exists or mode == 'w':
            writer.writeheader()
        writer.writerows(data)
# Локации для парсинга
locations = ['Талдом', 'Яхрома', 'Москва', 'Черноголовка', 'Одинцово', 'Электросталь', 
             'Щёлково', 'Дрезна', 'Клин', 'Егорьевск', 'Высоковск', 'Лыткарино', 
             'Чехов', 'Хотьково', 'Сергиев Посад', 'Павловский Посад', 'Красногорск', 
             'Химки', 'Дмитров', 'Яхрома', 'Долгопрудный', 'Троицк', 'Балашиха', 
             'Подольск', 'Мытищи', 'Люберцы', 'Королёв', 'Домодедово', 'Серпухов', 
             'Коломна', 'Раменское', 'Реутов', 'Пушкино', 'Жуковский', 'Видное', 
             'Орехово-Зуево', 'Ногинск', 'Воскресенск', 'Ивантеевка', 'Лобня', 
             'Дубна', 'Котельники', 'Фрязино', 'Дзержинский', 'Краснознаменск', 
             'Кашира', 'Звенигород', 'Истра', 'Красноармейск', 'Волоколамск', 
             'Озёры', 'Кубинка', 'Пущино', 'Руза', 'Краснозаводск', 
             'Пересвет', 'Можайск']
# Случайный прокси (В основном Армения и США)
def get_random_proxy():
    proxy_list = [
        '172.67.109.84:80',
        '198.41.220.73:80',
        '172.64.161.38:80',
        '104.20.156.139:80',
        '68.178.170.59:80',
        '185.162.228.242:80',
        '185.162.231.230:80'
    ]
    proxy = random.choice(proxy_list)
    return {"http": f"http://{proxy}", "https": f"http://{proxy}"}
# Главная функция с параметрами поиска 
def collect_real_estate_data(locations, deal_type="sale", rooms='all', start_page=26, end_page=101,
                             file_name='real_estate_data.csv', with_extra_data=False):
    all_data = []
    # Идентификация веб браузеров и ОС
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.66 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Gecko/20100101 Firefox/85.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.1 Safari/605.1.15",
    ]

    for location in locations:
        parser = cianparser.CianParser(location=location)
        print(f"Сбор данных для {location}...")

        for page in range(start_page, end_page + 1):
            user_agent = random.choice(user_agents)
            proxy = get_random_proxy()

            session = requests.Session()
            session.proxies.update(proxy)
            session.headers.update({"User-Agent": user_agent, "Referer": "https://cian.ru"})

            retries = 3  # Количество попыток
            for attempt in range(retries):
                try:
                    data = parser.get_flats(deal_type=deal_type, rooms=rooms,
                                            additional_settings={"start_page": page, "end_page": page})
                    break  # Если данные успешно получены, выход из цикла
                except requests.exceptions.RequestException as e:
                    print(f"Ошибка запроса страницы {page} для {location}: {e}. Попытка {attempt + 1}/{retries}")
                    time.sleep(5 + random.uniform(0, 5))  # Пауза перед повтором
                    if attempt == retries - 1:
                        logging.error(f"Не удалось получить данные с {page}-й страницы для {location}: {e}")
                        continue

            processed_data = []
            for flat in data:
                processed_flat = {
                    "author": flat.get("author", "Не указано"),
                    "author_type": flat.get("author_type", "Не указано"),
                    "url": flat.get("url", "Не указано"),
                    "location": flat.get("location", "Не указано"),
                    "deal_type": flat.get("deal_type", "sale"),
                    "accommodation_type": flat.get("accommodation_type", "flat"),
                    "floor": flat.get("floor", -1),
                    "floors_count": flat.get("floors_count", -1),
                    "rooms_count": flat.get("rooms_count", -1),
                    "total_meters": flat.get("total_meters", -1),
                    "price": flat.get("price", -1),
                    "district": flat.get("district", "Не указано"),
                    "street": flat.get("street", "Не указано"),"house_number": flat.get("house_number", "Не указано"),
                    "underground": flat.get("underground", "Не указано"),
                    "residential_complex": flat.get("residential_complex", "Не указано"),
                    "house_material_type": flat.get("house_material_type", "Не указано"),
                    "year_construction": flat.get("year_construction", -1)
                }

                if with_extra_data:
                    processed_flat["finishing_type"] = flat.get("finishing_type", "Не указано")
                    processed_flat["heating_type"] = flat.get("heating_type", "Не указано")

                processed_data.append(processed_flat)

            all_data.extend(processed_data)

            if len(all_data) >= 100:
                save_data_to_csv(all_data[:100], file_name)
                all_data = all_data[100:]

            time.sleep(random.uniform(2, 10))  # Увеличиние паузы между запросами 

        if all_data:
            save_data_to_csv(all_data, file_name)
            all_data = []

        print(f"Данные для {location} успешно собраны и сохранены в файл {file_name}")



collect_real_estate_data(locations=locations, deal_type="sale", rooms='all', start_page=1, end_page=54,
                         file_name="ParsedLogsCian.csv", with_extra_data=True)