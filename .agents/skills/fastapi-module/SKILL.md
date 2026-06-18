---
name: fastapi-module
description: Crear o modificar un módulo del backend FastAPI de ColAdventure. Úsalo SIEMPRE que trabajes en cualquier módulo del backend (auth, onboarding, generation, dashboard, assistant, admin, notifications) o cuando agregues un endpoint, un servicio, un repositorio o un schema, incluso si el usuario no menciona "módulo" explícitamente. Garantiza la cadena router→service→repository y las reglas multi-tenant.
---

# Módulo FastAPI (ColAdventure)

Todo módulo del backend sigue esta estructura y estas reglas. No te las saltes.

## Estructura

Cada módulo es un directorio en `backend/app/modules/<modulo>/` con exactamente:
- `router.py` — recibe el request, valida con Pydantic, llama al service. Nada de lógica de negocio ni de DB aquí.
- `service.py` — la lógica de negocio. Llama al repository. Llama a la IA solo vía un `AIProvider`.
- `repository.py` — el ÚNICO que habla con Supabase. Recibe `tenant_id` como parámetro obligatorio.
- `schemas.py` — modelos Pydantic de entrada/salida.

## Cadena obligatoria

`router → service → repository → DB`. Nunca saltes un eslabón:
- El router NUNCA llama a la DB.
- El service NUNCA llama a Supabase directo (siempre vía repository).
- Un módulo NUNCA importa el `repository` de otro módulo. Si necesitas datos de otro módulo, llama a su `service`.

## Reglas multi-tenant y de tipado

- Todo endpoint de escritura toma `tenant_id` del JWT (extraído por el middleware), NUNCA del body del request.
- El repository recibe `tenant_id` como parámetro explícito y obligatorio; nunca lo infiere solo.
- Todos los endpoints y funciones tipados con Pydantic. Prohibido `Any` o `dict` sin tipar.

## IA y prompts

- Cualquier llamada a un modelo pasa por la interfaz `AIProvider` (Strategy). Nunca el SDK de Gemini directo desde un service.
- Los prompts se cargan desde la tabla `prompt_versions` (solo uno activo por módulo). Nunca prompts inline en el código.

## Tests

- Cada módulo tiene sus tests en `backend/tests/<modulo>/`.
- Al menos un test de integración por endpoint.

## Esqueleto de referencia

```python
# router.py
@router.post("/", response_model=FooOut)
async def create_foo(payload: FooIn, tenant_id: str = Depends(get_tenant_id)):
    return await foo_service.create(payload, tenant_id)

# service.py
async def create(payload: FooIn, tenant_id: str) -> FooOut:
    # lógica de negocio; IA solo vía AIProvider
    return await foo_repository.insert(payload, tenant_id)

# repository.py
async def insert(payload: FooIn, tenant_id: str) -> FooOut:
    # único punto que habla con Supabase
    ...
```
