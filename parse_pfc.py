from googletrans import Translator
import requests


class NutritionixFood:
    def __init__(self, food: dict) -> None:
        self.food_name = food.get('food_name')
        self.brand_name = food.get('brand_name')
        self.serving_qty = food.get('serving_qty')
        self.serving_weight_grams = food.get('serving_weight_grams')
        self.nf_calories = food.get('nf_calories')
        self.nf_total_fat = food.get('nf_total_fat')
        self.nf_saturated_fat = food.get('nf_saturated_fat')
        self.nf_cholesterol = food.get('nf_cholesterol')
        self.nf_total_carbohydrate = food.get('nf_total_carbohydrate')
        self.nf_dietary_fiber = food.get('nf_dietary_fiber')
        self.nf_sugars = food.get('nf_sugars')
        self.nf_protein = food.get('nf_protein')
        self.nf_potassium = food.get('nf_potassium')
        self.nf_p = food.get('nf_p')
        self.full_nutrients = food.get('full_nutrients')
        self.photo_url = food.get('photo', {}).get('highres')
        self.barcode = food.get('upc')


def translate_from_rus_to_eng(text):
    translator = Translator()
    translated = translator.translate(text, src='ru', dest='en')
    return translated.text


def translate_from_eng_to_rus(text):
    translator = Translator()
    translated = translator.translate(text, src='en', dest='ru')
    return translated.text


def parse_pfc(query):
    query = translate_from_rus_to_eng(query)
    natural_url = 'https://trackapi.nutritionix.com/v2/natural/nutrients'
    headers = {
        "Content-Type": "application/json",
        "x-app-id": '98609f42',
        "x-app-key": '9f1ab67d6f8fb3d1d500d582e8f37054'
    }
    body = {
        "query": query,
        "timezone": "US/Eastern"
    }
    response = requests.post(natural_url, json=body, headers=headers)
    if response.status_code == 200:
        message = ''
        data = response.json()
        foods = data["foods"]
        result = [NutritionixFood(food) for food in foods]
        sum_weight = 0
        sum_calories = 0
        sum_protein = 0
        sum_fat = 0
        sum_carbohydrate = 0
        for product in result:
            message += (f"<b>{translate_from_eng_to_rus(product.food_name)}</b> {product.serving_weight_grams} г / "
                        f"{product.nf_calories} ккал\nБЖУ {product.nf_protein}/{product.nf_total_fat}/{product.nf_total_carbohydrate}\n")
            sum_weight += product.serving_weight_grams
            sum_calories += product.nf_calories
            sum_protein += product.nf_protein
            sum_fat += product.nf_total_fat
            sum_carbohydrate += product.nf_total_carbohydrate
        result = {'sum_weight': round(sum_weight), 'sum_calories': round(sum_calories), 'sum_protein': round(
            sum_protein),
                  'sum_fat':
                      round(sum_fat),
                            'sum_carbohydrate': round(sum_carbohydrate)}
        return message, result
    return 'Произошла ошибка при обработке запроса', None
