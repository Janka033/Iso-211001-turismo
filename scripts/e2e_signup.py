"""Registra la cuenta de prueba vía el flujo real de signup y entra al dashboard."""

import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

email, password, company, outdir = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
out = Path(outdir)
out.mkdir(parents=True, exist_ok=True)

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1440, "height": 900})

    page.goto("http://localhost:3000/login")
    page.wait_for_load_state("networkidle")

    # Cambiar a modo registro.
    page.click("text=Regístrate")
    page.wait_for_timeout(500)

    # El modo signup añade el campo de nombre de empresa (sin type explícito:
    # se localiza excluyendo email/password).
    page.locator('input:not([type="email"]):not([type="password"])').first.fill(company)
    page.fill('input[type="email"]', email)
    page.fill('input[type="password"]', password)
    page.screenshot(path=str(out / "05-signup-form.png"))
    page.click('button[type="submit"]')

    try:
        page.wait_for_url("**/dashboard", timeout=40000)
        page.wait_for_load_state("networkidle")
        page.screenshot(path=str(out / "06-dashboard-after-signup.png"), full_page=True)
        print("OK: dashboard tras signup ->", page.url)
    except Exception:
        page.screenshot(path=str(out / "06-signup-failed.png"), full_page=True)
        print("FALLO: url =", page.url)

    browser.close()
