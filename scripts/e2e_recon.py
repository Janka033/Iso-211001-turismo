"""Reconocimiento visual E2E: login real y capturas de dashboard/calidad/onboarding.

Uso: py scripts/e2e_recon.py <email> <password> <outdir>
Los servidores (3000/8000) deben estar corriendo.
"""

import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

email, password, outdir = sys.argv[1], sys.argv[2], sys.argv[3]
out = Path(outdir)
out.mkdir(parents=True, exist_ok=True)

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1440, "height": 900})

    # 1. Login (captura antes de enviar, para verificar la paleta del login).
    page.goto("http://localhost:3000/login")
    page.wait_for_load_state("networkidle")
    page.screenshot(path=str(out / "01-login.png"), full_page=True)

    page.fill('input[type="email"]', email)
    page.fill('input[type="password"]', password)
    page.click('button[type="submit"]')
    page.wait_for_url("**/dashboard", timeout=30000)
    page.wait_for_load_state("networkidle")
    page.screenshot(path=str(out / "02-dashboard.png"), full_page=True)

    # 2. Calidad.
    page.goto("http://localhost:3000/dashboard/calidad")
    page.wait_for_load_state("networkidle")
    page.screenshot(path=str(out / "03-calidad.png"), full_page=True)

    # 3. Onboarding.
    page.goto("http://localhost:3000/onboarding")
    page.wait_for_load_state("networkidle")
    page.screenshot(path=str(out / "04-onboarding.png"), full_page=True)

    browser.close()

print(f"OK: capturas en {out}")
