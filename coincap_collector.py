import requests

api_key = "139f371038c23b420a4450bf50e9cc902ef19028a6fd9069b0d7e83fb7ad6408"

url = "https://rest.coincap.io/v3/assets/bitcoin"

hearders = {
    "Authorization": f"Bearer {api_key}"
}

# GET 요청 보내기
response = requests.get(url, headers=hearders)

print(response.json())