"""Recorrido de humo por las pestañas del dashboard: captura cada una y
reporta errores de consola/red. Uso: py scripts/e2e_tabs_check.py <email> <pw> <empresa> <outdir>
"""

import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

email, password, company, outdir = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
out = Path(outdir)
out.mkdir(parents=True, exist_ok=True)

TABS = [
    ("/dashboard", "01-panel"),
    ("/dashboard/ruta", "02-ruta"),
    ("/dashboard/calidad", "03-calidad"),
    ("/dashboard/inventario", "04-inventario"),
    ("/campo", "05-campo"),
    ("/onboarding", "06-onboarding"),
]

errors: list[str] = []

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1440, "height": 900})
    page.on(
        "console",
        lambda m: errors.append(f"console[{m.type}] {m.text[:160]}")
        if m.type == "error"
        else None,
    )
    page.on("pageerror", lambda e: errors.append(f"pageerror {str(e)[:160]}"))
    page.on(
        "response",
        lambda r: errors.append(f"HTTP {r.status} {r.url[:120]}")
        if r.status >= 500
        else None,
    )

    page.goto("http://localhost:3000/login")
    page.wait_for_load_state("networkidle")
    page.click("text=Regístrate")
    page.wait_for_timeout(400)
    page.locator('input:not([type="email"]):not([type="password"])').first.fill(company)
    page.fill('input[type="email"]', email)
    page.fill('input[type="password"]', password)
    page.click('button[type="submit"]')
    page.wait_for_url("**/dashboard", timeout=40000)

    for path, name in TABS:
        page.goto(f"http://localhost:3000{path}")
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(700)
        page.screenshot(path=str(out / f"{name}.png"), full_page=False)
        print(f"{name}: ok")

    browser.close()

print("--- errores capturados:", len(errors))
for e in errors[:20]:
    print(" ", e)
