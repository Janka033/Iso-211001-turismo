"""Prueba de navegador de la Fase 3: signup QA → mapa de la ruta → chat con
barra de paso → celebración "Generar mi documento" → nodo generado en el mapa.

Uso: py scripts/e2e_ruta_fase3.py <email> <password> <empresa> <outdir>
"""

import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

email, password, company, outdir = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
out = Path(outdir)
out.mkdir(parents=True, exist_ok=True)

IDENTITY_MSG = (
    "Operamos en Santander, rio Fonce en San Gil. Alcance: rafting recreativo "
    "en el rio Fonce. 4 guias certificados. Equipo: 1 gerente y 4 guias. "
    "Representante legal Ana Ruiz, NIT 901.234.567-8, RNT vigente 12345. "
    "Nuestros objetivos de seguridad: reducir incidentes 20% a diciembre 2026 "
    "midiendo incidentes por salida cada mes (responsable el gerente), y "
    "capacitar al 100% de los guias en rescate antes de junio de 2027. La "
    "direccion se compromete a priorizar la seguridad con recursos y revision "
    "anual."
)

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1440, "height": 950})

    # 1. Signup (crea el tenant QA).
    page.goto("http://localhost:3000/login")
    page.wait_for_load_state("networkidle")
    page.click("text=Regístrate")
    page.wait_for_timeout(400)
    page.locator('input:not([type="email"]):not([type="password"])').first.fill(company)
    page.fill('input[type="email"]', email)
    page.fill('input[type="password"]', password)
    page.click('button[type="submit"]')
    page.wait_for_url("**/dashboard", timeout=40000)
    page.wait_for_load_state("networkidle")

    # 2. El mapa de la ruta recién nacido (todo pendiente, paso 1 en curso).
    page.goto("http://localhost:3000/dashboard/ruta")
    page.wait_for_selector("text=Camino a la certificación", timeout=20000)
    page.wait_for_timeout(800)
    page.screenshot(path=str(out / "01-ruta-inicial.png"), full_page=True)

    # 3. Onboarding: elegir actividad y mandar el turno de identidad.
    page.goto("http://localhost:3000/onboarding")
    page.wait_for_load_state("networkidle")
    page.click("text=Rafting")
    page.click("text=Comenzar")
    page.wait_for_selector("textarea", timeout=30000)
    page.screenshot(path=str(out / "02-chat-paso0.png"))
    page.fill("textarea", IDENTITY_MSG)
    page.press("textarea", "Enter")
    # La IA responde y el paso avanza; la celebración de objetivos aparece.
    page.wait_for_selector("text=Generar mi documento", timeout=90000)
    page.wait_for_timeout(600)
    page.screenshot(path=str(out / "03-chat-celebracion.png"))

    # 4. Generar desde el chat (celebración → burbuja de éxito).
    page.click("text=Generar mi documento")
    page.wait_for_selector("text=¡Generé tu", timeout=120000)
    page.wait_for_timeout(600)
    page.screenshot(path=str(out / "04-chat-generado.png"))

    # 5. El mapa refleja el documento generado (check verde).
    page.goto("http://localhost:3000/dashboard/ruta")
    page.wait_for_selector("text=Camino a la certificación", timeout=20000)
    page.wait_for_timeout(1000)
    page.screenshot(path=str(out / "05-ruta-con-generado.png"), full_page=True)

    print("OK: recorrido Fase 3 completo")
    browser.close()
