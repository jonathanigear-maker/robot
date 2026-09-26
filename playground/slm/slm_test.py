import requests

text = input("You: ")

data = {
    "messages": [
        {"role": "system", "content": "You are the brain of a small physical robot."},
        {"role": "user", "content": text}
    ]
}

response = requests.post(
    "http://localhost:8080/v1/chat/completions",
    json=data
)

print("Robot:", response.json()["choices"][0]["message"]["content"])