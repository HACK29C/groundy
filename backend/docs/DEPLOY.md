# Groundy — Despliegue en Google Cloud Run

FastAPI (sin cambios) + Cloud Run + Supabase + GEE + NASA POWER.
No se tocan `point_engine`, `rotation_score` ni `climate_tools`.
Cloud Build construye la imagen en la nube: **no necesitas Docker local**.

Proyecto GCP: `kinetic-anvil-457906-e8` (el mismo de GEE)
Servicio: `groundy-api` · Región sugerida: `us-central1`

> Ejecuta esto en tu PC (PowerShell), con `gcloud` ya autenticado en tu cuenta.
> La llave de GEE y la de Supabase viajan por **Secret Manager**, nunca en la imagen ni en el código.

## 1. Proyecto y APIs
```powershell
gcloud config set project kinetic-anvil-457906-e8
gcloud services enable run.googleapis.com cloudbuild.googleapis.com secretmanager.googleapis.com earthengine.googleapis.com
```

## 2. Crear los secretos

**GEE (desde tu archivo local):**
```powershell
gcloud secrets create gee-key --data-file=secrets/gee_key.json
```

**Supabase secret key (sin dejarla en el historial):**
```powershell
# 1) crea un archivo temporal con la llave (sb_secret_...), SIN salto de linea
Set-Content -NoNewline -Path sb.txt -Value "sb_secret_...TU_LLAVE..."
# 2) crea el secreto desde el archivo
gcloud secrets create supabase-service-key --data-file=sb.txt
# 3) borra el archivo
Remove-Item sb.txt
```

Si ya existe un secreto y quieres actualizar su valor, usa:
```powershell
gcloud secrets versions add gee-key --data-file=secrets/gee_key.json
```

## 3. Permiso para leer los secretos
La service account de runtime de Cloud Run (por defecto, la de Compute) necesita
leer los secretos. Averigua el número de proyecto y concede el permiso:
```powershell
$PN = gcloud projects describe kinetic-anvil-457906-e8 --format="value(projectNumber)"
$SA = "$PN-compute@developer.gserviceaccount.com"
gcloud secrets add-iam-policy-binding gee-key             --member="serviceAccount:$SA" --role="roles/secretmanager.secretAccessor"
gcloud secrets add-iam-policy-binding supabase-service-key --member="serviceAccount:$SA" --role="roles/secretmanager.secretAccessor"
```

## 4. Desplegar
```powershell
gcloud run deploy groundy-api `
  --source . `
  --region us-central1 `
  --allow-unauthenticated `
  --memory 1Gi --cpu 1 --timeout 300 --concurrency 8 `
  --set-env-vars "GEE_KEY_PATH=/secrets/gee_key.json,SUPABASE_URL=https://svaksbawrhndxyzugjjr.supabase.co,CORS_ORIGINS=*,PROC_VERSION=1.1,CACHE_COORD_DECIMALS=4,CACHE_TTL_DAYS=30" `
  --set-secrets "/secrets/gee_key.json=gee-key:latest,SUPABASE_SERVICE_KEY=supabase-service-key:latest"
```
- La primera vez puede pedir permiso para que Cloud Build construya: acepta.
- Al terminar imprime la **Service URL** (algo como `https://groundy-api-xxxx-uc.a.run.app`).

## 5. Probar en producción
```powershell
$URL = "https://<tu-service-url>"
curl "$URL/salud"        # gee:true, cache:true
curl "$URL/cultivos"
curl -Method POST "$URL/analizar/punto" -ContentType "application/json" -Body '{"lat":1.21,"lon":-77.28}'
```
- `/salud` debe mostrar `gee: true` y `cache: true`.
- La 1ª consulta de un punto tarda ~60 s (GEE); la 2ª idéntica vuelve al instante (`meta.fuente = "cache"`).

## 6. Conectar el frontend (Groundy)
En la app, apunta la URL base del API a la **Service URL** (por variable de entorno
del frontend, no escrita en el código). La lógica de consumo no cambia.

## Notas
- **CORS**: por ahora `*` (cualquiera puede llamar). Cuando el frontend tenga dominio fijo, cámbialo a ese dominio con otro `gcloud run services update ... --set-env-vars CORS_ORIGINS=https://tu-dominio`.
- **min-instances**: NO se activa por ahora (escala a cero = más barato). Si el arranque en frío molesta en la demo, se añade `--min-instances=1` (tiene costo).
- **Precalentar**: antes de presentar, consulta una vez cada punto del demo para que queden en caché y respondan al instante.
- **Redeploy** tras cambios de código: repite solo el paso 4.
