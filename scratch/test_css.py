import httpx

r = httpx.get("http://127.0.0.1:5173/src/styles/index.css")
print("Status:", r.status_code)
text = r.text
print("Length:", len(text))
print("Has .dark:", ".dark" in text)
idx = text.find(".dark")
print("Snippet around .dark:")
print(text[idx:idx+300])
