"""
💰 Expense Tracker Bot v2.0 — Telegram бот для трекинга расходов
Система 4 конвертов + Notion + Inline кнопки

Автор: tytopop
"""

import socket
_orig = socket.getaddrinfo
def _ipv4(*a, **k): return [r for r in _orig(*a, **k) if r[0] == socket.AF_INET]
socket.getaddrinfo = _ipv4

from dotenv import load_dotenv
load_dotenv()
import os, json, logging, sqlite3, requests
from datetime import datetime, timedelta
from pathlib import Path

BOT_TOKEN = os.getenv("BOT_TOKEN")
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
NOTION_DB = os.getenv("NOTION_DB")
ALLOWED_USER = int(os.getenv("ALLOWED_USER", "0"))

CATEGORIES = {"еда": "🍕 Еда", "транспорт": "🚌 Транспорт", "быт": "🏠 Быт", "здоровье": "💊 Здоровье", "одежда": "👕 Одежда", "связь": "📱 Связь", "развлечения": "🎬 Развлечения", "подарки": "🎁 Подарки", "другое": "📦 Другое"}
CAT_BUTTONS = [[("🍕 Еда","cat:еда"),("🚌 Транспорт","cat:транспорт"),("🏠 Быт","cat:быт")],[("💊 Здоровье","cat:здоровье"),("👕 Одежда","cat:одежда"),("📱 Связь","cat:связь")],[("🎬 Развлеч.","cat:развлечения"),("🎁 Подарки","cat:подарки"),("📦 Другое","cat:другое")]]
ALIASES = {"е":"еда","food":"еда","продукты":"еда","обед":"еда","ужин":"еда","завтрак":"еда","кофе":"еда","перекус":"еда","т":"транспорт","метро":"транспорт","такси":"транспорт","бензин":"транспорт","б":"быт","дом":"быт","хоз":"быт","з":"здоровье","аптека":"здоровье","врач":"здоровье","о":"одежда","с":"связь","инет":"связь","телефон":"связь","р":"развлечения","кино":"развлечения","д":"другое"}

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
log = logging.getLogger("bot")
API = f"https://api.telegram.org/bot{BOT_TOKEN}"
DB_PATH = Path(__file__).parent / "expenses.db"
user_states = {}

SETUP_STEPS = [("salary","💼 Введи свою зарплату (BYN):"),("spouse_income","👫 Доход жены/мужа (BYN, 0 если нет):"),("freelance_income","💻 Доход от фриланса (BYN, 0 если нет):"),("utilities","🏠 Коммуналка (BYN):"),("credit_1_name","🏦 Кредит 1 — название (или 'нет'):"),("credit_1_payment","💳 Кредит 1 — мин. платёж (BYN):"),("credit_2_name","🏦 Кредит 2 — название (или 'нет'):"),("credit_2_payment","💳 Кредит 2 — мин. платёж (BYN):"),("credit_3_name","🏦 Кредит 3 — название (или 'нет'):"),("credit_3_payment","💳 Кредит 3 — мин. платёж (BYN):"),("deposit","💰 Сумма на депозит (BYN, 0 если нет):"),("extra_credit_payment","⚡ Доп. погашение кредитов (BYN, 0 если нет):"),("reserve_pct","🛡️ % резерва от дохода (например 10, 0 если нет):")]

def send_msg(chat_id, text, kb=None):
    p = {"chat_id":chat_id,"text":text,"parse_mode":"HTML"}
    if kb: p["reply_markup"]=json.dumps({"inline_keyboard":kb})
    try: requests.post(f"{API}/sendMessage",json=p,timeout=10)
    except Exception as e: log.error(f"Send: {e}")

def answer_cb(cb_id, text=""):
    try: requests.post(f"{API}/answerCallbackQuery",json={"callback_query_id":cb_id,"text":text},timeout=5)
    except: pass

def set_bot_commands():
    try: requests.post(f"{API}/setMyCommands",json={"commands":[{"command":"menu","description":"📋 Главное меню"},{"command":"budget","description":"💰 Конверт недели"},{"command":"today","description":"📅 Сегодня"},{"command":"week","description":"📊 Неделя"},{"command":"month","description":"📊 Месяц"},{"command":"setup","description":"⚙️ Настройка"},{"command":"config","description":"📋 Настройки"},{"command":"undo","description":"↩️ Отменить"},{"command":"help","description":"❓ Помощь"}]},timeout=10)
    except: pass

def menu_kb():
    return [[{"text":"💸 Расход","callback_data":"a:expense"},{"text":"💵 Доход","callback_data":"a:income"}],[{"text":"💰 Конверт","callback_data":"a:budget"},{"text":"📅 Сегодня","callback_data":"a:today"}],[{"text":"📊 Неделя","callback_data":"a:week"},{"text":"📊 Месяц","callback_data":"a:month"}],[{"text":"⚙️ Настройка","callback_data":"a:setup"},{"text":"↩️ Отменить","callback_data":"a:undo"}]]

def cat_kb():
    kb=[]
    for row in CAT_BUTTONS: kb.append([{"text":l,"callback_data":d} for l,d in row])
    kb.append([{"text":"❌ Отмена","callback_data":"a:cancel"}])
    return kb

def skip_kb(): return [[{"text":"⏭ Без комментария","callback_data":"a:skip"}],[{"text":"❌ Отмена","callback_data":"a:cancel"}]]
def back_kb(): return [[{"text":"📋 Меню","callback_data":"a:menu"}]]

# === DB ===
def init_db():
    c=sqlite3.connect(DB_PATH)
    c.execute("CREATE TABLE IF NOT EXISTS expenses (id INTEGER PRIMARY KEY AUTOINCREMENT,user_id INTEGER,category TEXT,amount REAL,comment TEXT DEFAULT '',created_at TEXT DEFAULT (datetime('now','localtime')),synced INTEGER DEFAULT 0)")
    c.execute("CREATE TABLE IF NOT EXISTS budget_config (user_id INTEGER,key TEXT,value TEXT,updated_at TEXT DEFAULT (datetime('now','localtime')),PRIMARY KEY(user_id,key))")
    c.commit();c.close()

def set_cfg(uid,k,v):
    c=sqlite3.connect(DB_PATH);c.execute("INSERT OR REPLACE INTO budget_config(user_id,key,value,updated_at)VALUES(?,?,?,datetime('now','localtime'))",(uid,k,str(v)));c.commit();c.close()

def get_all_cfg(uid):
    c=sqlite3.connect(DB_PATH);r=c.execute("SELECT key,value FROM budget_config WHERE user_id=?",(uid,)).fetchall();c.close();return dict(r)

def weekly_budget(uid):
    cfg=get_all_cfg(uid)
    if not cfg: return 0
    inc=float(cfg.get("salary",0))+float(cfg.get("spouse_income",0))+float(cfg.get("freelance_income",0))
    fix=float(cfg.get("utilities",0))
    for i in range(1,4):
        n=cfg.get(f"credit_{i}_name","нет")
        if n and n.lower()!="нет": fix+=float(cfg.get(f"credit_{i}_payment",0))
    dep=float(cfg.get("deposit",0));ext=float(cfg.get("extra_credit_payment",0));res=inc*float(cfg.get("reserve_pct",0))/100
    return max(round((inc-fix-dep-ext-res)/4),0)

def add_exp(uid,cat,amt,comm=""): c=sqlite3.connect(DB_PATH);c.execute("INSERT INTO expenses(user_id,category,amount,comment)VALUES(?,?,?,?)",(uid,cat,amt,comm));c.commit();c.close()
def add_inc(uid,amt,comm=""): c=sqlite3.connect(DB_PATH);c.execute("INSERT INTO expenses(user_id,category,amount,comment)VALUES(?,?,?,?)",(uid,"_income",amt,comm));c.commit();c.close()

def _monday(): return (datetime.now()-timedelta(days=datetime.now().weekday())).strftime("%Y-%m-%d")

def today_rows(uid):
    c=sqlite3.connect(DB_PATH);r=c.execute("SELECT category,amount,comment,created_at FROM expenses WHERE user_id=? AND date(created_at)=? ORDER BY created_at",(uid,datetime.now().strftime("%Y-%m-%d"))).fetchall();c.close();return r

def week_exp(uid):
    c=sqlite3.connect(DB_PATH);m=_monday()
    r=c.execute("SELECT category,SUM(amount) FROM expenses WHERE user_id=? AND category!='_income' AND date(created_at)>=? GROUP BY category ORDER BY SUM(amount) DESC",(uid,m)).fetchall()
    t=c.execute("SELECT COALESCE(SUM(amount),0) FROM expenses WHERE user_id=? AND category!='_income' AND date(created_at)>=?",(uid,m)).fetchone()[0];c.close();return r,t

def week_total(uid):
    c=sqlite3.connect(DB_PATH);t=c.execute("SELECT COALESCE(SUM(amount),0) FROM expenses WHERE user_id=? AND category!='_income' AND date(created_at)>=?",(uid,_monday())).fetchone()[0];c.close();return t

def week_inc(uid):
    c=sqlite3.connect(DB_PATH);t=c.execute("SELECT COALESCE(SUM(amount),0) FROM expenses WHERE user_id=? AND category='_income' AND date(created_at)>=?",(uid,_monday())).fetchone()[0];c.close();return t

def month_exp(uid):
    c=sqlite3.connect(DB_PATH);ms=datetime.now().strftime("%Y-%m-01")
    r=c.execute("SELECT category,SUM(amount) FROM expenses WHERE user_id=? AND category!='_income' AND date(created_at)>=? GROUP BY category ORDER BY SUM(amount) DESC",(uid,ms)).fetchall()
    t=c.execute("SELECT COALESCE(SUM(amount),0) FROM expenses WHERE user_id=? AND category!='_income' AND date(created_at)>=?",(uid,ms)).fetchone()[0];c.close();return r,t

def month_inc(uid):
    c=sqlite3.connect(DB_PATH);ms=datetime.now().strftime("%Y-%m-01")
    r=c.execute("SELECT amount,comment,created_at FROM expenses WHERE user_id=? AND category='_income' AND date(created_at)>=? ORDER BY created_at",(uid,ms)).fetchall()
    t=sum(x[0] for x in r);c.close();return r,t

def undo(uid):
    c=sqlite3.connect(DB_PATH);r=c.execute("SELECT id,category,amount,comment FROM expenses WHERE user_id=? ORDER BY id DESC LIMIT 1",(uid,)).fetchone()
    if r: c.execute("DELETE FROM expenses WHERE id=?",(r[0],));c.commit()
    c.close();return r

def notion_send(cat,amt,comm,dt):
    if not NOTION_TOKEN or not NOTION_DB: return False
    try:
        cn="💵 Доход" if cat=="_income" else CATEGORIES.get(cat,cat)
        r=requests.post("https://api.notion.com/v1/pages",headers={"Authorization":f"Bearer {NOTION_TOKEN}","Notion-Version":"2022-06-28","Content-Type":"application/json"},json={"parent":{"database_id":NOTION_DB},"properties":{"Комментарий":{"title":[{"text":{"content":comm or cn}}]},"Date":{"date":{"start":dt}},"Категория":{"select":{"name":cn}},"Сумма":{"number":amt if cat=="_income" else -amt},"Неделя":{"number":datetime.now().isocalendar()[1]}}},timeout=10)
        return r.status_code==200
    except Exception as e: log.warning(f"Notion: {e}");return False

def parse_exp(text):
    p=text.strip().split(maxsplit=2)
    if len(p)<2: return None,None,None
    cat=ALIASES.get(p[0].lower(),p[0].lower())
    if cat not in CATEGORIES: return None,None,None
    try:
        a=float(p[1].replace(",","."))
        if a<=0 or a>10000: return None,None,None
    except: return None,None,None
    return cat,a,p[2] if len(p)>2 else ""

# === SHOW ===
def show_budget(uid,cid):
    w=weekly_budget(uid)
    if w==0: send_msg(cid,"⚙️ Сначала настрой бюджет!",[[{"text":"⚙️ Настроить","callback_data":"a:setup"}]]);return
    ei=week_inc(uid);eff=w+ei;sp=week_total(uid);rem=eff-sp
    pct=min(sp/eff*100,100) if eff else 0;f=min(int(pct/100*20),20);bar="█"*f+"░"*(20-f)
    st="✅" if rem>=0 else "🚨 ПРЕВЫШЕН!";dl=7-datetime.now().weekday();d=rem/dl if dl>0 and rem>0 else 0
    m=f"💰 <b>Конверт недели</b>\n\nБазовый: {w} BYN\n"
    if ei>0: m+=f"Доп. доходы: +{ei:.0f} BYN\nИтого: <b>{eff:.0f} BYN</b>\n"
    m+=f"Потрачено: {sp:.2f} BYN\n[{bar}] {pct:.0f}%\n\nОстаток: <b>{rem:.2f} BYN</b> {st}\n📅 До конца недели: {dl} дн.\n💡 Можно: <b>{d:.2f} BYN/день</b>"
    send_msg(cid,m,back_kb())

def show_today(uid,cid):
    rows=today_rows(uid)
    if not rows: send_msg(cid,"📭 Сегодня расходов нет 💪",back_kb());return
    exps=[r for r in rows if r[0]!="_income"];incs=[r for r in rows if r[0]=="_income"];lines=[]
    for _,a,cm,ts in incs:
        t=ts.split(" ")[1][:5] if " " in ts else "";lines.append(f"  {t} 💵 +<b>{a:.2f}</b>"+(f" ({cm})" if cm else ""))
    for cat,a,cm,ts in exps:
        t=ts.split(" ")[1][:5] if " " in ts else "";lines.append(f"  {t} {CATEGORIES.get(cat,cat)} — <b>{a:.2f}</b>"+(f" ({cm})" if cm else ""))
    te=sum(r[1] for r in exps);ti=sum(r[1] for r in incs)
    m=f"📅 <b>Сегодня:</b>\n"+"\n".join(lines)+f"\n\n💸 Расходы: <b>{te:.2f} BYN</b>"
    if ti>0: m+=f"\n💵 Доходы: <b>+{ti:.2f} BYN</b>"
    send_msg(cid,m,back_kb())

def show_week(uid,cid):
    rows,total=week_exp(uid);ei=week_inc(uid)
    if not rows and ei==0: send_msg(cid,"📭 На этой неделе записей нет.",back_kb());return
    w=weekly_budget(uid);eff=w+ei;rem=eff-total;st="✅" if rem>=0 else "🔴"
    lines=[f"  {CATEGORIES.get(c,c)} — <b>{a:.2f}</b>" for c,a in rows]
    m=f"📊 <b>Эта неделя:</b>\n"
    if ei>0: m+=f"  💵 Доп. доходы: +{ei:.2f}\n"
    m+="\n".join(lines)+f"\n\n💸 Расходы: <b>{total:.2f}</b>"
    m+=f"\nБюджет: {w}"+(f" + {ei:.0f} = {eff:.0f}" if ei>0 else "")+" BYN"
    m+=f"\n{st} Остаток: <b>{rem:.2f} BYN</b>"
    send_msg(cid,m,back_kb())

def show_month(uid,cid):
    rows,total=month_exp(uid);ir,it=month_inc(uid)
    if not rows and not ir: send_msg(cid,"📭 В этом месяце записей нет.",back_kb());return
    w=weekly_budget(uid);mb=w*4;eff=mb+it;rem=eff-total;st="✅" if rem>=0 else "🔴";lines=[]
    if ir:
        lines.append("<b>💵 Доходы:</b>")
        for a,cm,_ in ir: lines.append(f"  +{a:.2f} — {cm or 'без описания'}")
        lines.append("")
    if rows:
        lines.append("<b>💸 Расходы:</b>")
        lines.extend([f"  {CATEGORIES.get(c,c)} — <b>{a:.2f}</b>" for c,a in rows])
    m=f"📊 <b>Этот месяц:</b>\n"+"\n".join(lines)+f"\n\n💸 Расходы: <b>{total:.2f}</b>"
    if it>0: m+=f"\n💵 Доп. доходы: <b>+{it:.2f}</b>"
    m+=f"\nБюджет: {mb}"+(f" + {it:.0f} = {eff:.0f}" if it>0 else "")+" BYN"
    m+=f"\n{st} Остаток: <b>{rem:.2f} BYN</b>"
    send_msg(cid,m,back_kb())

def show_config(uid,cid):
    cfg=get_all_cfg(uid)
    if not cfg: send_msg(cid,"⚙️ Бюджет не настроен.",[[{"text":"⚙️ Настроить","callback_data":"a:setup"}]]);return
    w=weekly_budget(uid);inc=float(cfg.get("salary",0))+float(cfg.get("spouse_income",0))+float(cfg.get("freelance_income",0))
    fix=float(cfg.get("utilities",0))
    for i in range(1,4):
        n=cfg.get(f"credit_{i}_name","нет")
        if n and n.lower()!="нет": fix+=float(cfg.get(f"credit_{i}_payment",0))
    dep=float(cfg.get("deposit",0));ext=float(cfg.get("extra_credit_payment",0));rp=float(cfg.get("reserve_pct",0));res=inc*rp/100;lb=inc-fix-dep-ext-res
    send_msg(cid,f"⚙️ <b>Текущий бюджет:</b>\n\n📊 Доход: {inc:.0f}\n🔒 Обязательные: {fix:.0f}\n💰 Накопления: {dep+ext+res:.0f}\n━━━━━━━━━━━━━━━━\n✉️ На жизнь: <b>{lb:.0f}/мес</b>\n📅 Конверт: <b>{w} BYN/нед</b>\n📅 В день: <b>~{round(lb/30)} BYN</b>",
             [[{"text":"⚙️ Пересчитать","callback_data":"a:setup"},{"text":"📋 Меню","callback_data":"a:menu"}]])

# === SAVE ===
def save_exp(uid,cid,cat,amt,comm):
    add_exp(uid,cat,amt,comm);s=notion_send(cat,amt,comm,datetime.now().strftime("%Y-%m-%d"));ic="☁️" if s else "💾"
    w=weekly_budget(uid);ei=week_inc(uid);eff=w+ei;sp=week_total(uid);rem=eff-sp
    st=f"✅ Остаток: {rem:.2f}" if rem>=0 else f"🔴 Превышение: {abs(rem):.2f}"
    send_msg(cid,f"{CATEGORIES[cat]} <b>{amt:.2f} BYN</b>"+(f" — {comm}" if comm else "")+f"\n{st} BYN {ic}",menu_kb())

def save_inc(uid,cid,amt,comm):
    add_inc(uid,amt,comm);s=notion_send("_income",amt,comm,datetime.now().strftime("%Y-%m-%d"));ic="☁️" if s else "💾"
    w=weekly_budget(uid);ei=week_inc(uid)
    send_msg(cid,f"💵 <b>+{amt:.2f} BYN</b>"+(f" — {comm}" if comm else "")+f"\n✅ Конверт: {w} + {ei:.0f} = <b>{w+ei:.0f} BYN</b> {ic}",menu_kb())

# === SETUP ===
def handle_setup(uid,cid,text):
    st=user_states.get(uid)
    if not st or st.get("mode")!="setup": return False
    si=st["step"];key=SETUP_STEPS[si][0]
    if key.endswith("_name") and text.lower().strip() in ("нет","0","-","no",""):
        cn=key.split("_")[1];set_cfg(uid,key,"нет");set_cfg(uid,f"credit_{cn}_payment","0")
        ns=next((i for i,s in enumerate(SETUP_STEPS) if s[0]=="deposit"),len(SETUP_STEPS))
    elif key.endswith("_name"):
        set_cfg(uid,key,text.strip());ns=si+1
    else:
        try: v=float(text.replace(",",".").strip());set_cfg(uid,key,v);ns=si+1
        except: send_msg(cid,"❌ Введи число:");return True
    if ns>=len(SETUP_STEPS):
        del user_states[uid];w=weekly_budget(uid);cfg=get_all_cfg(uid)
        inc=float(cfg.get("salary",0))+float(cfg.get("spouse_income",0))+float(cfg.get("freelance_income",0))
        fix=float(cfg.get("utilities",0));cl=[]
        for i in range(1,4):
            n=cfg.get(f"credit_{i}_name","нет")
            if n and n.lower()!="нет": p=float(cfg.get(f"credit_{i}_payment",0));cl.append(f"    {n}: {p:.0f}");fix+=p
        dep=float(cfg.get("deposit",0));ext=float(cfg.get("extra_credit_payment",0));rp=float(cfg.get("reserve_pct",0));res=inc*rp/100;lb=inc-fix-dep-ext-res;dy=round(lb/30)
        m=f"✅ <b>Бюджет настроен!</b>\n\n📊 <b>Доходы:</b> {inc:.0f} BYN\n  Зарплата: {float(cfg.get('salary',0)):.0f}\n"
        if float(cfg.get("spouse_income",0))>0: m+=f"  Супруг(а): {float(cfg.get('spouse_income',0)):.0f}\n"
        if float(cfg.get("freelance_income",0))>0: m+=f"  Фриланс: {float(cfg.get('freelance_income',0)):.0f}\n"
        m+=f"\n🔒 <b>Обязательные:</b> {fix:.0f} BYN\n  Коммуналка: {float(cfg.get('utilities',0)):.0f}\n"
        if cl: m+="  Кредиты:\n"+"\n".join(cl)+"\n"
        m+=f"\n💰 <b>Накопления:</b> {dep+ext+res:.0f} BYN\n"
        if dep>0: m+=f"  Депозит: {dep:.0f}\n"
        if ext>0: m+=f"  Ускорение: {ext:.0f}\n"
        if res>0: m+=f"  Резерв {rp:.0f}%: {res:.0f}\n"
        m+=f"\n✉️ <b>На жизнь:</b>\n  Месяц: <b>{lb:.0f} BYN</b>\n  Неделя: <b>{w} BYN</b>\n  День: <b>~{dy} BYN</b>"
        if lb<0: m+=f"\n\n🚨 Расходы > доходы на {abs(lb):.0f} BYN!"
        send_msg(cid,m,menu_kb())
    else:
        user_states[uid]={"mode":"setup","step":ns};send_msg(cid,SETUP_STEPS[ns][1])
    return True

# === CALLBACK ===
def handle_cb(cb):
    cid_=cb["id"];d=cb.get("data","");msg=cb.get("message",{});cid=msg.get("chat",{}).get("id");uid=cb.get("from",{}).get("id")
    if not cid or not uid: return
    if ALLOWED_USER and uid!=ALLOWED_USER: return
    answer_cb(cid_)
    if d=="a:menu": send_msg(cid,"📋 <b>Главное меню</b>\n\nВыбери действие или напиши расход:",menu_kb())
    elif d=="a:expense": user_states[uid]={"mode":"exp_cat"};send_msg(cid,"💸 <b>Выбери категорию:</b>",cat_kb())
    elif d=="a:income": user_states[uid]={"mode":"inc_amt"};send_msg(cid,"💵 <b>Введи сумму дохода (BYN):</b>",[[{"text":"❌ Отмена","callback_data":"a:cancel"}]])
    elif d=="a:budget": show_budget(uid,cid)
    elif d=="a:today": show_today(uid,cid)
    elif d=="a:week": show_week(uid,cid)
    elif d=="a:month": show_month(uid,cid)
    elif d=="a:setup": user_states[uid]={"mode":"setup","step":0};send_msg(cid,f"⚙️ <b>Настройка бюджета</b>\n\n/cancel для отмены\n\n{SETUP_STEPS[0][1]}")
    elif d=="a:config": show_config(uid,cid)
    elif d=="a:undo":
        r=undo(uid)
        if r: _,cat,amt,cm=r;l="💵 Доход" if cat=="_income" else CATEGORIES.get(cat,cat);send_msg(cid,f"↩️ Удалено: {l} — {amt:.2f}"+(f" ({cm})" if cm else ""),back_kb())
        else: send_msg(cid,"Нечего отменять 🤷",back_kb())
    elif d=="a:cancel":
        if uid in user_states: del user_states[uid]
        send_msg(cid,"❌ Отменено.",menu_kb())
    elif d=="a:skip":
        s=user_states.get(uid,{});mo=s.get("mode","")
        if mo=="exp_comm": del user_states[uid];save_exp(uid,cid,s["cat"],s["amt"],"")
        elif mo=="inc_comm": del user_states[uid];save_inc(uid,cid,s["amt"],"")
    elif d.startswith("cat:"):
        cat=d[4:];user_states[uid]={"mode":"exp_amt","cat":cat}
        send_msg(cid,f"{CATEGORIES[cat]} — <b>введи сумму (BYN):</b>",[[{"text":"❌ Отмена","callback_data":"a:cancel"}]])

# === MESSAGE ===
def handle(msg):
    cid=msg["chat"]["id"];uid=msg["from"]["id"];text=msg.get("text","").strip()
    if not text: return
    if ALLOWED_USER and uid!=ALLOWED_USER: return
    s=user_states.get(uid,{});mo=s.get("mode","")
    if text.lower()=="/cancel":
        if uid in user_states: del user_states[uid]
        send_msg(cid,"❌ Отменено.",menu_kb());return
    if mo=="setup": handle_setup(uid,cid,text);return
    if mo=="exp_amt":
        try:
            a=float(text.replace(",","."))
            if a<=0 or a>10000: raise ValueError
            user_states[uid]={"mode":"exp_comm","cat":s["cat"],"amt":a}
            send_msg(cid,f"{CATEGORIES[s['cat']]} {a:.2f} BYN\n\n💬 Комментарий:",skip_kb())
        except: send_msg(cid,"❌ Введи корректную сумму:")
        return
    if mo=="exp_comm": del user_states[uid];save_exp(uid,cid,s["cat"],s["amt"],text);return
    if mo=="inc_amt":
        try:
            a=float(text.replace(",","."))
            if a<=0 or a>100000: raise ValueError
            user_states[uid]={"mode":"inc_comm","amt":a}
            send_msg(cid,f"💵 +{a:.2f} BYN\n\n💬 Комментарий:",skip_kb())
        except: send_msg(cid,"❌ Введи корректную сумму:")
        return
    if mo=="inc_comm": del user_states[uid];save_inc(uid,cid,s["amt"],text);return

    if text in ("/start","/menu"):
        w=weekly_budget(uid)
        if w==0: send_msg(cid,"👋 <b>Привет! Я трекер расходов.</b>\n\nНажми кнопку:",[[{"text":"⚙️ Настроить бюджет","callback_data":"a:setup"}]])
        else: send_msg(cid,f"👋 Конверт: <b>{w} BYN/нед</b>",menu_kb())
        return
    if text=="/budget": show_budget(uid,cid);return
    if text=="/today": show_today(uid,cid);return
    if text=="/week": show_week(uid,cid);return
    if text=="/month": show_month(uid,cid);return
    if text=="/config": show_config(uid,cid);return
    if text=="/setup": user_states[uid]={"mode":"setup","step":0};send_msg(cid,f"⚙️ <b>Настройка</b>\n\n/cancel для отмены\n\n{SETUP_STEPS[0][1]}");return
    if text=="/undo":
        r=undo(uid)
        if r: _,cat,amt,cm=r;l="💵 Доход" if cat=="_income" else CATEGORIES.get(cat,cat);send_msg(cid,f"↩️ {l} — {amt:.2f}"+(f" ({cm})" if cm else ""),back_kb())
        else: send_msg(cid,"Нечего отменять 🤷",back_kb())
        return
    if text=="/help":
        send_msg(cid,"📖 <b>Как пользоваться:</b>\n\n🔘 <b>💸 Расход</b> → категория → сумма\n🔘 <b>💵 Доход</b> → сумма\n\nИли текстом:\n  <code>еда 15.5 обед</code>\n  <code>+500 премия</code>\n\nАлиасы: е, т, б, з, о, с, р, д",menu_kb());return
    if text.startswith("/"): return

    if text.startswith("+"):
        p=text[1:].strip().split(maxsplit=1)
        if not p: send_msg(cid,"❓ <code>+500 премия</code>");return
        try:
            a=float(p[0].replace(",","."))
            if a<=0: raise ValueError
        except: send_msg(cid,"❓ <code>+500 премия</code>");return
        save_inc(uid,cid,a,p[1] if len(p)>1 else "");return

    cat,amt,comm=parse_exp(text)
    if cat:
        w=weekly_budget(uid)
        if w==0: send_msg(cid,"⚙️ Сначала настрой бюджет!",[[{"text":"⚙️ Настроить","callback_data":"a:setup"}]]);return
        save_exp(uid,cid,cat,amt,comm);return

    send_msg(cid,"❓ Используй меню или:\n<code>еда 12.5</code> / <code>+500 премия</code>",menu_kb())

def main():
    init_db();set_bot_commands();log.info("Bot v2.0 started")
    offset=None
    while True:
        try:
            p={"timeout":30}
            if offset: p["offset"]=offset
            r=requests.get(f"{API}/getUpdates",params=p,timeout=35).json()
            for u in r.get("result",[]):
                offset=u["update_id"]+1
                if "message" in u: handle(u["message"])
                elif "callback_query" in u: handle_cb(u["callback_query"])
        except Exception as e: log.error(f"Error: {e}");import time;time.sleep(5)

if __name__=="__main__": main()
