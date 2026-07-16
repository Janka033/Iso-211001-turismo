"""Diagnóstico del login: envía credenciales y captura lo que pase."""

import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

email, password, outdir = sys.argv[1], sys.argv[2], sys.argv[3]
out = Path(outdir)
out.mkdir(parents=True, exist_ok=True)

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1440, "height": 900})
    logs: list[str] = []
    page.on("console", lambda m: logs.append(f"[{m.type}] {m.text}"))

    page.goto("http://localhost:3000/login")
    page.wait_for_load_state("networkidle")

    page.fill('input[type="email"]', email)
    page.fill('input[type="password"]', password)
    page.click('button[type="submit"]')
    page.wait_for_timeout(8000)

    page.screenshot(path=str(out / "login-after-submit.png"), full_page=True)
    print("URL:", page.url)
    # Texto de error visible (si la UI lo pintó).
    for sel in ["[class*=rose]", "[class*=red]", "p"]:
        for el in page.locator(sel).all()[:12]:
            t = (el.text_content() or "").strip()
            if t and ("error" in t.lower() or "inválid" in t.lower() or "credencial" in t.lower() or "incorrect" in t.lower()):
                print("UI:", t)
    print("CONSOLE (últimos 10):")
    for line in logs[-10:]:
        print(" ", line)

    browser.close()
