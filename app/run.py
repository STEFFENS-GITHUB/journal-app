import requests

response = requests.get("http://localhost:8000/api/user/1")
print("Headers:", response.headers, "\n")
print("Body: ", response.json())