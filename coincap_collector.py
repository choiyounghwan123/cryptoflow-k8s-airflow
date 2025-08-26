import requests

url = "https://api.binance.com/api/v3/ticker/price"

# GET 요청 보내기
response = requests.get(url)
print(response.json())