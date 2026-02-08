# Documentación Integral del Backend (Estado Real)

Fecha: 2026-02-08

## 1. Objetivo y alcance
Este documento describe el backend implementado hoy en `backend/app/**`, con foco en onboarding técnico y mantenimiento. La fuente de verdad usada para todas las afirmaciones fue:
- Código: `backend/app/**`, `backend/scripts/**`
- Tests: `backend/tests/**`

Se evitó documentar comportamiento no implementado.

## 2. Snapshot arquitectónico real
Arquitectura principal (establecida en código):
- `Route` HTTP (FastAPI): validaciones de entrada, authN/authZ, mapeo a HTTP errors.
- `UseCase`: orquestación de caso de uso.
- `Service`: reglas de negocio/transacción de dominio.
- `Repository`: acceso a SQLModel/DB.
- Modelos de dominio/API: contratos `Create/Update/Public` y modelos `table=True`.

Referencias:
- `backend/app/main.py`
- `backend/app/api/main.py`
- `backend/app/api/deps.py`
- `backend/app/models.py`

## 3. Boot, runtime y componentes transversales
Startup/shutdown real:
- En startup se ejecuta `resume_pending_jobs()` y luego se inicia `RateExtractionScheduler`.
- En shutdown se detiene el scheduler (`await scheduler.stop()`).

Referencias:
- `backend/app/main.py`
- `backend/app/domains/upload_jobs/service/job_resumption.py`
- `backend/app/domains/currency/service/rate_scheduler.py`
- `backend/tests/test_lifespan.py`

Dependencias base:
- JWT + usuario activo por `get_current_user`.
- `SessionDep` usa `get_db()` y engine lazy de `provider.py`.

Referencias:
- `backend/app/api/deps.py`
- `backend/app/core/security.py`
- `backend/app/pkgs/database/provider.py`

## 4. Inventario de endpoints y prefijos
Conteo actual de operaciones HTTP en rutas: **60** (`@router.get/post/put/patch/delete`).

Prefijo global:
- Todos los routers públicos cuelgan de `settings.API_V1_STR` (`/api/v1`) vía `app.include_router(api_router, prefix=settings.API_V1_STR)`.

Routers de dominio:
- `/users`, `/credit-cards`, `/card-statements`, `/payments`, `/transactions`, `/currency`, `/upload-jobs`, `/tags`, `/transaction-tags`, `/rules`, `/utils`, `login/*`.

Ruta privada condicional:
- `/private/users/` solo se monta en `ENVIRONMENT == "local"`.

Referencias:
- `backend/app/main.py`
- `backend/app/api/main.py`
- `backend/app/api/routes/private.py`
- `backend/app/core/config.py`

## 5. Autorización y ownership (comportamiento real)
### 5.1 Patrón general
Patrón dominante:
- AuthN: `CurrentUser` (JWT válido + usuario activo).
- AuthZ: checks de ownership mayormente en route layer, con algunos casos por usecase/repository.

Referencias:
- `backend/app/api/deps.py`
- `backend/app/api/routes/**/*.py`

### 5.2 Confirmado por dominio
Users:
- List/create/update/delete admin por `Depends(get_current_active_superuser)` o check explícito.
- Usuario normal puede leer/editar su propio perfil y contraseña.

Referencias:
- `backend/app/api/routes/users/list_users.py`
- `backend/app/api/routes/users/create_user.py`
- `backend/app/api/routes/users/update_user.py`
- `backend/app/api/routes/users/delete_user.py`
- `backend/tests/api/routes/test_users.py`

Credit cards / statements / tags / transaction-tags (single) / payments:
- Predominio de checks por ownership del recurso (o superuser bypass), con matices listados en riesgos.

Referencias:
- `backend/app/api/routes/credit_cards/*.py`
- `backend/app/api/routes/card_statements/*.py`
- `backend/app/api/routes/tags/*.py`
- `backend/app/api/routes/transaction_tags/get_tags.py`
- `backend/app/api/routes/payments/*.py`

Rules:
- Ownership de reglas se aplica en servicio (`RuleService._check_user_owns_rule`) y las rutas traducen a 404.

Referencias:
- `backend/app/domains/rules/service/rule_service.py`
- `backend/app/api/routes/rules/*.py`
- `backend/tests/api/routes/test_rules.py`

Upload jobs:
- `GET /upload-jobs/{job_id}` devuelve 404 si el job no pertenece al usuario autenticado.
- No hay bypass de superuser en ese endpoint.

Referencias:
- `backend/app/api/routes/upload_jobs/get_job.py`
- `backend/tests/api/routes/test_upload_jobs.py`

## 6. Flujo de upload asíncrono (PDF) y modos de falla
### 6.1 Entrada y enqueue
`POST /card-statements/upload`:
- Valida filename y extensión `.pdf`.
- Lee bytes y valida tamaño máximo 25MB.
- Verifica ownership de la tarjeta (excepto superuser).
- Calcula SHA-256, busca duplicado por `(user_id, file_hash)`.
- Sube PDF a storage.
- Crea `upload_job` en `PENDING`.
- Encola `process_upload_job(...)` en `BackgroundTasks`.

Referencias:
- `backend/app/api/routes/card_statements/upload_statement.py`
- `backend/app/domains/upload_jobs/domain/models.py`
- `backend/app/domains/upload_jobs/repository/upload_job_repository.py`
- `backend/tests/api/routes/card_statements/test_upload_statement.py`
- `backend/tests/e2e/test_upload_workflow.py`

### 6.2 Procesamiento en background
`process_upload_job(...)`:
- Intenta pasar a `PROCESSING` (con reintentos cuando el job todavía no está visible por commit race).
- Extrae con modelo primario; si falla, incrementa retry y usa fallback.
- Si extracción completa: import atómico + `COMPLETED`.
- Si extracción parcial: import atómico parcial + `PARTIAL`.
- Si falla: `FAILED` con mensaje sanitizado.
- Luego aplica reglas en modo no bloqueante.

Referencias:
- `backend/app/domains/upload_jobs/usecases/process_upload/usecase.py`
- `backend/tests/domains/upload_jobs/usecases/test_process_upload.py`

### 6.3 Reanudación en restart
`resume_pending_jobs()`:
- Reencola jobs `PENDING`.
- Reencola jobs `PROCESSING` stale (>30 min), primero reseteando a `PENDING`.
- Si no puede recuperar PDF de storage, marca `FAILED`.
- Usa `asyncio.create_task(...)` durante startup.

Referencias:
- `backend/app/domains/upload_jobs/service/job_resumption.py`
- `backend/app/main.py`

## 7. Atomicidad e idempotencia (garantías reales)
Atomicidad garantizada:
- Import de statement + transacciones en una misma transacción (`with session.begin()`).
- Incluye actualización condicional de límite de tarjeta dentro de ese bloque.

Referencias:
- `backend/app/domains/upload_jobs/service/atomic_import.py`
- `backend/tests/domains/upload_jobs/usecases/test_process_upload.py`
- `backend/tests/integration/test_credit_limits_flow.py`

Idempotencia garantizada:
- Upload dedupe por `UniqueConstraint(user_id, file_hash)` + manejo de carrera (`DuplicateFileError`).
- Rule application idempotente por `transaction_tags` con PK compuesta y `create_or_ignore`.

Referencias:
- `backend/app/domains/upload_jobs/domain/models.py`
- `backend/app/domains/upload_jobs/repository/upload_job_repository.py`
- `backend/app/domains/transaction_tags/domain/models.py`
- `backend/app/domains/transaction_tags/repository/transaction_tag_repository.py`
- `backend/app/domains/rules/usecases/apply_rules/usecase.py`

Límites de la garantía (importante):
- El estado del `upload_job` y la aplicación de reglas no forman parte de la misma transacción que el import atómico de statement/transacciones.

Referencias:
- `backend/app/domains/upload_jobs/usecases/process_upload/usecase.py`
- `backend/app/domains/upload_jobs/service/atomic_import.py`

## 8. Semántica del motor de reglas
Validación de reglas (`RuleService`):
- En create: requiere al menos una condición y una acción.
- En update: si se envía `conditions`/`actions`, no puede ser lista vacía.
- Verifica existencia de `tag_id` y que no esté soft-deleted.
- Matriz campo-operador:
  - `payee/description`: `contains`, `equals`
  - `amount`: `equals`, `gt`, `lt`, `between`
  - `date`: `equals`, `before`, `after`, `between`
- `between` requiere `value_secondary`.

Referencias:
- `backend/app/domains/rules/service/rule_service.py`
- `backend/tests/crud/rules/test_rule_service.py`
- `backend/tests/api/routes/test_rules.py`

Evaluación (`RuleEvaluationService`):
- Ordena condiciones por `position`.
- Evalúa izquierda a derecha usando `logical_operator` de cada condición subsiguiente.
- `contains/equals` string case-insensitive.
- Parse inválido en amount/date retorna no-match (`False`).

Referencias:
- `backend/app/domains/rules/service/rule_evaluation_service.py`
- `backend/tests/crud/rules/test_rule_evaluation_service.py`

Scope de `POST /rules/apply`:
- Si `transaction_ids` está presente, tiene precedencia.
- Si no, usa `statement_id`.
- Si request vacío, aplica a **todas** las transacciones del usuario.

Referencias:
- `backend/app/domains/rules/usecases/apply_rules/usecase.py`
- `backend/tests/api/routes/test_apply_rules.py`

## 9. Currency: conversión, consulta, extracción y scheduler
### 9.1 Endpoints DB-backed (`domains/currency`)
Conversión (`/currency/convert`, `/currency/convert/batch`):
- Solo USD/ARS.
- Toma tasa de DB (exact date -> closest date; sin fecha -> latest).
- `from == to` retorna identidad con rate 1.

Consulta de tasas (`/currency/rates`):
- Modos: latest, date (con fallback closest), range.
- Para ARS->USD invierte spread (buy = 1/sell; sell = 1/buy).
- Si no hay tasas retorna 200 con lista vacía (no 404).

Referencias:
- `backend/app/api/routes/currency/convert.py`
- `backend/app/api/routes/currency/rates.py`
- `backend/app/domains/currency/service/currency_conversion_service.py`
- `backend/app/domains/currency/repository/exchange_rate_repository.py`
- `backend/tests/api/routes/test_currency_convert.py`
- `backend/tests/api/routes/test_currency_rates.py`

### 9.2 Extracción manual y scheduler
Extracción manual (`POST /currency/rates/extract`):
- Requiere superuser.
- Encola background job que extrae de Cronista y hace upsert por `rate_date`.

Scheduler diario:
- Corre en loop async con horario UTC configurable.
- Se inicia en startup y se detiene en shutdown.
- Si una corrida falla, loguea y continúa el loop (no cae todo el scheduler).

Referencias:
- `backend/app/api/routes/currency/extract.py`
- `backend/app/domains/currency/service/exchange_rate_extractor.py`
- `backend/app/domains/currency/service/rate_scheduler.py`
- `backend/tests/api/routes/test_currency_extract.py`
- `backend/tests/domains/currency/test_rate_scheduler.py`

### 9.3 Segundo camino de conversión en upload
El import de upload usa `app/pkgs/currency` (cliente HTTP externo `exchangerate-api`) para `convert_balance` y para convertir límites en `AtomicImportService`.

Referencias:
- `backend/app/pkgs/currency/client.py`
- `backend/app/pkgs/currency/service.py`
- `backend/app/domains/upload_jobs/service/atomic_import.py`

## 10. Riesgos técnicos vigentes (confirmados)
1. `GET /transactions` sin `statement_id` no aplica filtro de ownership por usuario.
Referencias: `backend/app/api/routes/transactions/list_transactions.py`, `backend/tests/api/routes/test_list_transactions.py`.

2. `POST /transaction-tags/batch` devuelve relaciones por IDs sin validar ownership de cada transacción.
Referencias: `backend/app/api/routes/transaction_tags/get_tags_batch.py`.

3. `POST /payments` valida `payment.user_id` pero no valida que `statement_id` pertenezca a ese usuario.
Referencias: `backend/app/api/routes/payments/create_payment.py`, `backend/app/domains/payments/service/payment_service.py`.

4. `POST /card-statements/` captura `Exception` genérica; un `HTTPException(403)` por ownership termina devolviendo 404.
Referencias: `backend/app/api/routes/card_statements/create_statement.py`.

5. En `process_upload_job` se usa `time.sleep` dentro de función async durante el retry inicial de estado.
Referencias: `backend/app/domains/upload_jobs/usecases/process_upload/usecase.py`.

6. `ConditionOperator` define `gte/lte`, y el evaluador los implementa para montos, pero la validación de create/update no los permite.
Referencias: `backend/app/domains/rules/domain/models.py`, `backend/app/domains/rules/service/rule_service.py`, `backend/app/domains/rules/service/rule_evaluation_service.py`.

7. Superuser no tiene bypass para leer jobs ajenos (`/upload-jobs/{id}`), siempre 404 si no coincide `job.user_id`.
Referencias: `backend/app/api/routes/upload_jobs/get_job.py`.

## 11. Testing útil para mantenimiento
Cobertura fuerte en:
- Upload + job lifecycle + errores sanitizados.
- Reglas (validación, evaluación, apply, aislamiento entre usuarios, auto-apply al crear transacción).
- Currency (convert, rates, extract, scheduler).
- Ownership puntual en `transactions` (cuando hay `statement_id`) y `transaction-tags/transaction/{id}`.

Referencias:
- `backend/tests/domains/upload_jobs/usecases/test_process_upload.py`
- `backend/tests/e2e/test_upload_workflow.py`
- `backend/tests/api/routes/test_apply_rules.py`
- `backend/tests/crud/rules/test_rule_service.py`
- `backend/tests/crud/rules/test_rule_evaluation_service.py`
- `backend/tests/api/routes/test_currency_convert.py`
- `backend/tests/api/routes/test_currency_rates.py`
- `backend/tests/api/routes/test_currency_extract.py`
- `backend/tests/domains/currency/test_rate_scheduler.py`

## 12. Diagramas
Se mantienen en:
- `backend/docs/diagrams/arquitectura-backend.md`
- `backend/docs/diagrams/secuencia-carga-resumen.md`
- `backend/docs/diagrams/secuencia-aplicar-reglas.md`
- `backend/docs/diagrams/actividad-procesamiento-carga.md`
- `backend/docs/diagrams/actividad-aplicacion-reglas.md`
- `backend/docs/diagrams/casos-uso-backend.md`

Estado en esta auditoría:
- No fue necesario ajustar Mermaid para mantener consistencia con el texto actualizado (los cambios fueron de precisión operativa y edge-cases no modelados a nivel de diagrama).

## Validation report
### Corrected inconsistencies
- Se corrigió la descripción de ownership para reflejar excepciones reales en `transactions list` sin `statement_id` y `transaction-tags/batch`.
  Referencias: `backend/app/api/routes/transactions/list_transactions.py`, `backend/app/api/routes/transaction_tags/get_tags_batch.py`, `backend/tests/api/routes/test_list_transactions.py`.
- Se corrigió el flujo de `rules/apply` para request vacío: aplica a todas las transacciones del usuario.
  Referencias: `backend/app/domains/rules/usecases/apply_rules/usecase.py`, `backend/tests/api/routes/test_apply_rules.py`.
- Se corrigió el detalle de `card-statements create`: ownership deny puede terminar en 404 por `except Exception` amplio.
  Referencia: `backend/app/api/routes/card_statements/create_statement.py`.
- Se aclaró que `/upload-jobs/{id}` no otorga bypass a superuser.
  Referencias: `backend/app/api/routes/upload_jobs/get_job.py`, `backend/tests/api/routes/test_upload_jobs.py`.
- Se aclaró que hay dos caminos de conversión de moneda (DB-backed y HTTP externo) con responsabilidades distintas.
  Referencias: `backend/app/domains/currency/**`, `backend/app/pkgs/currency/**`, `backend/app/domains/upload_jobs/service/atomic_import.py`.

### Added missing sections
- Inventario explícito de prefijos/rutas y condición de montaje de `/private`.
- Lifecycle completo de upload job incluyendo reanudación de stale jobs en startup y fallas de recuperación de PDF.
- Sección de límites de atomicidad/idempotencia (qué sí y qué no queda bajo la misma transacción).
- Semántica detallada del motor de reglas (validación, evaluación y precedencia de scope).
- Riesgos técnicos confirmados con referencias de código/tests.

### Remaining uncertainties
- No hay pruebas dedicadas para `resume_pending_jobs()` que validen exhaustivamente escenarios concurrentes de reencolado y errores de storage en startup.
  Referencias: `backend/app/domains/upload_jobs/service/job_resumption.py`, `backend/tests/test_lifespan.py`.
- No hay pruebas API específicas para `POST /transaction-tags/batch` que documenten el comportamiento esperado de ownership.
  Referencias: `backend/app/api/routes/transaction_tags/get_tags_batch.py`, `backend/tests/api/routes/test_transaction_tags.py`.
- No hay pruebas API que confirmen el comportamiento de `POST /payments` cuando `statement_id` pertenece a otro usuario.
  Referencias: `backend/app/api/routes/payments/create_payment.py`, `backend/app/domains/payments/service/payment_service.py`.
