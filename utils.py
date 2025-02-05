import requests
import config

def get_pay_link(amount):
    headers = {"Crypto-Pay-API-Token": config.CRYPTOPAY_API_TOKEN}
    data = {"asset": "USDT", "amount": amount}
    response = requests.post('https://pay.crypt.bot/api/createInvoice', headers=headers, json=data)
    if response.ok:
        response_data = response.json()
        return response_data['result']['pay_url'], response_data['result']['invoice_id']
    return None, None

def check_payment_status(invoice_id):
    headers = {
        "Crypto-Pay-API-Token": config.CRYPTOPAY_API_TOKEN,
        "Content-Type": "application/json"
    }
    response = requests.post('https://pay.crypt.bot/api/getInvoices', headers=headers, json={})
    
    if response.ok:
        return response.json()
    else:
        print(f"Ошибка при запросе к API: {response.status_code}, {response.text}")
        return None

def get_usd_to_rub_rate():
    response = requests.get('https://api.exchangerate-api.com/v4/latest/USD')
    if response.ok:
        data = response.json()
        return data['rates']['RUB']
    else:
        print(f"Ошибка при запросе курса обмена: {response.status_code}, {response.text}")
        return None
