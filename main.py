from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import uvicorn
from datetime import datetime
import asyncio
from typing import Dict, List
import random

app = FastAPI(title="بوت التداول الكمي - Multi Agent")
templates = Jinja2Templates(directory="templates")

# ======================
# حالة النظام (Paper Trading)
# ======================
state = {
    "balance": 25000.00,
    "available": 25000.00,
    "equity": 25000.00,
    "realized_pnl": 0.0,
    "unrealized_pnl": 0.0,
    "open_trades": [],
    "closed_trades": [],
    "win_rate": 0.0,
    "total_trades": 0,
    "wins": 0,
    "losses": 0,
    "max_drawdown": 0.0,
    "is_running": False,
    "start_time": None,
    "agents_status": {
        "Scanner": "نشط",
        "Analyzer": "نشط",
        "Risk Manager": "نشط",
        "Executor": "متوقف",
        "Logger": "نشط",
        "Equity": "نشط"
    },
    "live_log": [],
    "current_pair": "BTC/USDT",
    "current_price": 67500.0,
    "last_update": datetime.now().strftime("%H:%M:%S")
}

def add_log(action: str, pair: str, reason: str, color: str = "white"):
    log_entry = {
        "time": datetime.now().strftime("%H:%M:%S"),
        "action": action,
        "pair": pair,
        "reason": reason,
        "color": color
    }
    state["live_log"].insert(0, log_entry)
    if len(state["live_log"]) > 30:
        state["live_log"] = state["live_log"][:30]

# ======================
# محاكاة بسيطة للوكلاء (Paper)
# ======================
async def run_agents():
    while True:
        if state["is_running"]:
            # محاكاة تغيير السعر
            change = random.uniform(-0.4, 0.5)
            state["current_price"] = round(state["current_price"] * (1 + change/100), 2)
            state["last_update"] = datetime.now().strftime("%H:%M:%S")

            # محاكاة قرار عشوائي بسيط (لاحقاً نستبدله باستراتيجية حقيقية)
            if random.random() < 0.15 and len(state["open_trades"]) < 3:
                side = random.choice(["شراء", "بيع"])
                size = round(random.uniform(0.1, 0.4), 3)
                entry = state["current_price"]
                
                trade = {
                    "id": len(state["closed_trades"]) + len(state["open_trades"]) + 1,
                    "pair": state["current_pair"],
                    "side": side,
                    "entry": entry,
                    "size": size,
                    "time": datetime.now().strftime("%H:%M:%S"),
                    "reason": "إشارة زخم قوية من Analyzer + تأكيد الحجم"
                }
                state["open_trades"].append(trade)
                state["agents_status"]["Executor"] = "LIVE"
                
                add_log("ENTER", state["current_pair"], trade["reason"], "green")
            
            # إغلاق صفقات بشكل عشوائي
            if state["open_trades"] and random.random() < 0.1:
                trade = state["open_trades"].pop(0)
                exit_price = state["current_price"]
                pnl = (exit_price - trade["entry"]) * trade["size"] if trade["side"] == "شراء" else (trade["entry"] - exit_price) * trade["size"]
                pnl = round(pnl, 2)
                
                trade["exit"] = exit_price
                trade["pnl"] = pnl
                trade["exit_time"] = datetime.now().strftime("%H:%M:%S")
                
                state["closed_trades"].insert(0, trade)
                state["realized_pnl"] = round(state["realized_pnl"] + pnl, 2)
                state["balance"] = round(25000 + state["realized_pnl"], 2)
                state["available"] = state["balance"]
                state["equity"] = state["balance"]
                state["total_trades"] += 1
                
                if pnl > 0:
                    state["wins"] += 1
                    add_log("EXIT", trade["pair"], f"تحقيق هدف | ربح {pnl} ر.س", "green")
                else:
                    state["losses"] += 1
                    add_log("EXIT", trade["pair"], f"وقف خسارة | خسارة {pnl} ر.س", "red")
                
                if state["total_trades"] > 0:
                    state["win_rate"] = round((state["wins"] / state["total_trades"]) * 100, 1)
                
                state["agents_status"]["Executor"] = "نشط"

        await asyncio.sleep(8)  # كل 8 ثواني دورة

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(run_agents())

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    return templates.TemplateResponse("index.html", {
        "request": request,
        "state": state
    })

@app.post("/start")
async def start_bot():
    state["is_running"] = True
    state["start_time"] = datetime.now().strftime("%H:%M:%S")
    state["agents_status"]["Executor"] = "LIVE"
    add_log("SYSTEM", "SYSTEM", "تم تشغيل المحرك التجريبي", "blue")
    return {"status": "started"}

@app.post("/stop")
async def stop_bot():
    state["is_running"] = False
    state["agents_status"]["Executor"] = "متوقف"
    add_log("SYSTEM", "SYSTEM", "تم إيقاف المحرك", "orange")
    return {"status": "stopped"}

@app.get("/api/state")
async def get_state():
    return state

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=10000, reload=True)
