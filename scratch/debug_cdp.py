import asyncio
import subprocess
import time
import json
import httpx
import websockets

CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

async def run_inspection():
    proc = subprocess.Popen([
        CHROME_PATH,
        "--headless=new",
        "--remote-debugging-port=9222",
        "http://127.0.0.1:5173/?theme=dark"
    ])
    
    try:
        await asyncio.sleep(2)
        r = httpx.get("http://127.0.0.1:9222/json", timeout=5)
        tabs = r.json()
        target = tabs[0]
        ws_url = target["webSocketDebuggerUrl"]
        
        async with websockets.connect(ws_url) as ws:
            async def evaluate(expr):
                req = {
                    "id": 1,
                    "method": "Runtime.evaluate",
                    "params": {"expression": expr, "returnByValue": True}
                }
                await ws.send(json.dumps(req))
                res = await ws.recv()
                data = json.loads(res)
                return data.get("result", {}).get("result", {}).get("value")
            
            print("1. html class:", await evaluate("document.documentElement.className"))
            print("2. html data-theme:", await evaluate("document.documentElement.getAttribute('data-theme')"))
            print("3. --color-bg on :root:", await evaluate("getComputedStyle(document.documentElement).getPropertyValue('--color-bg')"))
            print("4. body background:", await evaluate("getComputedStyle(document.body).backgroundColor"))
            print("5. #hero background:", await evaluate("document.querySelector('#hero') ? getComputedStyle(document.querySelector('#hero')).backgroundColor : 'no #hero'"))
            print("6. card background:", await evaluate("document.querySelector('#dashboard-preview > div') ? getComputedStyle(document.querySelector('#dashboard-preview > div')).backgroundColor : 'no card'"))
            print("7. body color:", await evaluate("getComputedStyle(document.body).color"))
            
            # Now let's click the theme toggle!
            print("\n--- Clicking ThemeToggle ---")
            await evaluate("document.querySelector('button[role=\"switch\"]').click()")
            await asyncio.sleep(0.5)
            print("After click html class:", await evaluate("document.documentElement.className"))
            print("After click --color-bg:", await evaluate("getComputedStyle(document.documentElement).getPropertyValue('--color-bg')"))
            print("After click body background:", await evaluate("getComputedStyle(document.body).backgroundColor"))

            # Now let's click it again!
            print("\n--- Clicking ThemeToggle again ---")
            await evaluate("document.querySelector('button[role=\"switch\"]').click()")
            await asyncio.sleep(0.5)
            print("After 2nd click html class:", await evaluate("document.documentElement.className"))
            print("After 2nd click --color-bg:", await evaluate("getComputedStyle(document.documentElement).getPropertyValue('--color-bg')"))
            print("After 2nd click body background:", await evaluate("getComputedStyle(document.body).backgroundColor"))
            
    finally:
        proc.terminate()

asyncio.run(run_inspection())
