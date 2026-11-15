"""
Groundy API — cache-first sobre Supabase (tabla analysis_cache).

- Tolerante a fallos: ante cualquier problema de Supabase, get() devuelve miss
  y put() no lanza; el API sigue en vivo. PERO los fallos quedan REGISTRADOS
  (logging) con el codigo HTTP / tipo de error, nunca con la llave ni el payload.
- Clave determinista SHA-256 (tipo, geometria, datasets+periodo, params, version).
- Solo se guardan resultados validos (lo decide quien llama a put()).
- Coalescing por clave (por proceso).

Usa requests (ya es dependencia). No agrega dependencias nuevas.
"""
import hashlib
import json
import logging
import threading
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone

import requests

from . import config

log = logging.getLogger("groundy.cache")

_TIMEOUT = 8  # segundos por llamada a Supabase

_locks_guard = threading.Lock()
_locks = {}


@contextmanager
def key_lock(cache_key):
    with _locks_guard:
        lock = _locks.get(cache_key)
        if lock is None:
            lock = threading.Lock()
            _locks[cache_key] = lock
    lock.acquire()
    try:
        yield
    finally:
        lock.release()


def _round_coords(coords, d):
    return [[round(float(x), d), round(float(y), d)] for x, y in coords]


def build_key(kind, lat=None, lon=None, coords=None, extra=None):
    d = config.CACHE_COORD_DECIMALS
    geom = _round_coords(coords, d) if kind == "area" else [round(float(lon), d), round(float(lat), d)]
    identidad = {
        "kind": kind, "geom": geom, "data": config.DATA_SIGNATURE,
        "proc_version": config.PROC_VERSION, "decimals": d, "extra": extra or {},
    }
    canon = json.dumps(identidad, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canon.encode("utf-8")).hexdigest()


def _headers():
    return {
        "apikey": config.SUPABASE_SERVICE_KEY,
        "Authorization": "Bearer " + config.SUPABASE_SERVICE_KEY,
        "Content-Type": "application/json",
    }


def _url():
    return config.SUPABASE_URL + "/rest/v1/" + config.CACHE_TABLE


def get(cache_key):
    """Fila vigente y valida, o None (miss / vencida / invalida / error / cache off)."""
    if not config.CACHE_ENABLED:
        return None
    try:
        r = requests.get(
            _url(), headers=_headers(),
            params={"cache_key": "eq." + cache_key, "select": "*", "limit": "1"},
            timeout=_TIMEOUT,
        )
        if r.status_code != 200:
            log.warning("cache.get http=%s (clave=%s...)", r.status_code, cache_key[:8])
            return None
        rows = r.json()
        if not rows:
            return None
        row = rows[0]
        if not row.get("is_valid", False):
            return None
        exp = row.get("expires_at")
        if exp:
            exp_dt = datetime.fromisoformat(exp.replace("Z", "+00:00"))
            if datetime.now(timezone.utc) >= exp_dt:
                return None
        return row
    except Exception as e:
        log.warning("cache.get fallo: %s (clave=%s...)", type(e).__name__, cache_key[:8])
        return None


def put(cache_key, kind, payload, lat=None, lon=None, params=None, source=None):
    """Upsert de un resultado VALIDO. Devuelve (created_at, expires_at) ISO."""
    now = datetime.now(timezone.utc)
    exp = now + timedelta(days=config.CACHE_TTL_DAYS)
    created_iso, expires_iso = now.isoformat(), exp.isoformat()
    if not config.CACHE_ENABLED:
        return created_iso, expires_iso
    row = {
        "cache_key": cache_key, "kind": kind, "lat": lat, "lon": lon,
        "params": params or {}, "proc_version": config.PROC_VERSION,
        "source": source, "payload": payload, "is_valid": True,
        "created_at": created_iso, "expires_at": expires_iso, "hits": 0,
    }
    try:
        r = requests.post(
            _url(),
            headers={**_headers(), "Prefer": "resolution=merge-duplicates,return=minimal"},
            data=json.dumps(row), timeout=_TIMEOUT,
        )
        if r.status_code not in (200, 201, 204):
            # cuerpo acotado para depurar RLS/permenisos, sin credenciales
            log.warning("cache.put http=%s detalle=%s (clave=%s...)",
                        r.status_code, (r.text or "")[:200], cache_key[:8])
    except Exception as e:
        log.warning("cache.put fallo: %s (clave=%s...)", type(e).__name__, cache_key[:8])
    return created_iso, expires_iso


def _delete(cache_key):
    """Borra una fila (solo lo usa selftest para limpiar)."""
    if not config.CACHE_ENABLED:
        return
    try:
        requests.delete(_url(), headers=_headers(),
                        params={"cache_key": "eq." + cache_key}, timeout=_TIMEOUT)
    except Exception:
        pass


def selftest():
    """Prueba REAL contra Supabase: put -> get -> delete, sin tocar GEE.
    Devuelve un dict con el resultado de cada paso. No expone la llave."""
    st = config.cache_status()
    if not config.CACHE_ENABLED:
        return {"ok": False, "paso": "config", "detalle": st}
    key = "selftest:" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%f")
    muestra = {"climate": {"prueba": True}, "nota": "selftest groundy"}
    # PUT
    try:
        r = requests.post(
            _url(), headers={**_headers(), "Prefer": "resolution=merge-duplicates,return=minimal"},
            data=json.dumps({
                "cache_key": key, "kind": "punto", "lat": 0.0, "lon": 0.0,
                "params": {"selftest": True}, "proc_version": config.PROC_VERSION,
                "source": "selftest", "payload": muestra, "is_valid": True,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "expires_at": (datetime.now(timezone.utc) + timedelta(days=1)).isoformat(),
                "hits": 0,
            }), timeout=_TIMEOUT,
        )
        if r.status_code not in (200, 201, 204):
            return {"ok": False, "paso": "put", "http": r.status_code,
                    "detalle": (r.text or "")[:200], "pista": _pista(r.status_code)}
    except Exception as e:
        return {"ok": False, "paso": "put", "error": type(e).__name__,
                "detalle": "no se pudo conectar a Supabase"}
    # GET
    row = get(key)
    if row is None:
        _delete(key)
        return {"ok": False, "paso": "get", "detalle": "put ok pero get no recupero la fila"}
    coincide = row.get("payload") == muestra
    _delete(key)  # limpiar
    return {"ok": bool(coincide), "paso": "completo",
            "put_get_coincide": coincide, "tabla": config.CACHE_TABLE}


def _pista(http):
    return {
        401: "llave invalida o ausente (apikey/Authorization)",
        403: "RLS bloqueo la operacion: NO estas usando la service_role (¿usaste la anon/publishable?)",
        404: "tabla no encontrada: revisa CACHE_TABLE o el esquema",
    }.get(http, "revisa URL, tabla y llave service_role")
