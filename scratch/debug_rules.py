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
            
            expr = """
            (() => {
                const el = document.body;
                const hero = document.querySelector('#hero');
                const card = document.querySelector('#dashboard-preview > div');
                
                function inspectRules(element) {
                    const matched = [];
                    for (const sheet of document.styleSheets) {
                        try {
                            for (const rule of sheet.cssRules) {
                                if (rule.selectorText && element.matches(rule.selectorText)) {
                                    matched.push({
                                        selector: rule.selectorText,
                                        cssText: rule.cssText
                                    });
                                }
                            }
                        } catch (e) {}
                    }
                    return matched;
                }
                
                return {
                    bodyBgRules: inspectRules(el).filter(r => r.cssText.includes('background')),
                    heroBgRules: inspectRules(hero).filter(r => r.cssText.includes('background')),
                    cardBgRules: inspectRules(card).filter(r => r.cssText.includes('background')),
                };
            })()
            """
            info = await evaluate(expr)
            print("BODY RULES:", json.dumps(info["bodyBgRules"], indent=2))
            print("HERO RULES:", json.dumps(info["heroBgRules"], indent=2))
            print("CARD RULES:", json.dumps(info["cardBgRules"], indent=2))
    finally:
        proc.terminate()

asyncio.run(run_inspection())
