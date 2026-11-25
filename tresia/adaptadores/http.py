"""Adaptadores HTTP sin dependencias: Gemini (API de pago) y Ollama (verificador)."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

from tresia.adaptadores.base import Adaptador, AdaptadorError


def _post_json(url: str, cuerpo: dict, cabeceras: dict, tiempo: float) -> dict:
    datos = json.dumps(cuerpo).encode("utf-8")
    peticion = urllib.request.Request(url, data=datos, method="POST",
                                      headers={"Content-Type": "application/json", **cabeceras})
    try:
        with urllib.request.urlopen(peticion, timeout=tiempo) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        detalle = e.read().decode("utf-8", errors="replace")[:500]
        raise AdaptadorError(f"HTTP {e.code}: {detalle}") from e
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        raise AdaptadorError(f"Sin respuesta: {getattr(e, 'reason', e)}") from e
    except json.JSONDecodeError as e:
        raise AdaptadorError(f"Respuesta no JSON: {e}") from e


def leer_clave(definicion: dict) -> str | None:
    """Variable de entorno o almacén de credenciales de Windows (si ``keyring`` está
    instalado). La clave nunca se escribe en disco ni en mensajes."""
    if (nombre := definicion.get("clave_env")) and os.environ.get(nombre):
        return os.environ[nombre]
    try:
        import keyring  # opcional
    except ImportError:
        return None
    return keyring.get_password(definicion.get("clave_servicio", "tresia"), definicion.get("clave_usuario", "gemini"))


class AdaptadorGemini(Adaptador):
    """API de pago de Gemini (no la gratuita). La clave va en cabecera, no en la URL."""

    def __init__(self, definicion: dict):
        super().__init__(definicion)
        self.modelo = definicion.get("modelo", "")
        self.url_base = definicion.get("url_base", "").rstrip("/")

    def disponible(self) -> tuple[bool, str]:
        if not self.modelo:
            return False, "Falta el modelo de Gemini en perfiles/pc.local.toml."
        if not leer_clave(self.definicion):
            return False, f"No hay clave de Gemini (variable {self.definicion.get('clave_env')} o almacén de credenciales)."
        return True, ""

    def _llamar(self, prompt: str) -> tuple[str, str]:
        ok, motivo = self.disponible()
        if not ok:
            raise AdaptadorError(motivo)
        url = f"{self.url_base}/models/{self.modelo}:generateContent"
        cuerpo = {"contents": [{"role": "user", "parts": [{"text": prompt}]}],
                  "generationConfig": {"temperature": self.definicion.get("temperatura", 0.7)}}
        datos = _post_json(url, cuerpo, {"x-goog-api-key": leer_clave(self.definicion)}, self.tiempo_maximo)
        try:
            partes = datos["candidates"][0]["content"]["parts"]
        except (KeyError, IndexError, TypeError):
            motivo = datos.get("promptFeedback") or datos.get("candidates", [{}])[0].get("finishReason", "sin contenido")
            raise AdaptadorError(f"Gemini no devolvió texto: {motivo}")
        texto = "".join(p.get("text", "") for p in partes)
        return texto, json.dumps(datos, ensure_ascii=False)


def estimar_tokens(texto: str) -> int:
    """Estimación prudente sin tokenizador: unos 3 caracteres por token. Sobrestima
    el inglés (≈4) para no pasarse del contexto; el árabe queda cerca de lo real."""
    return len(texto) // 3 + 1


class AdaptadorOllama(Adaptador):
    """Ollama por HTTP (``/api/chat``, sin streaming, salida JSON).

    El servidor fija el contexto (8192 tokens) y Ollama recorta en silencio lo que
    no cabe. Por eso: se presupuesta antes de enviar, no se manda ``num_ctx`` ni
    ``keep_alive``, y un recorte detectado después cuenta como fallo."""

    def __init__(self, definicion: dict):
        super().__init__(definicion)
        self.modelo = definicion.get("modelo", "")
        self.url_base = definicion.get("url_base", "").rstrip("/")
        self.contexto = int(definicion.get("contexto", 8192))
        self.num_predict = int(definicion.get("num_predict", 2000))
        self.max_prompt = int(definicion.get("max_tokens_prompt", self.contexto - self.num_predict - 200))

    def cabe(self, prompt: str) -> tuple[bool, str]:
        estimados = estimar_tokens(prompt)
        if estimados > self.max_prompt:
            return False, (f"El prompt (≈{estimados} tokens) no cabe en el contexto del verificador del servidor "
                           f"(máximo {self.max_prompt}). Hay que trocear la tarea o usar el respaldo.")
        return True, ""

    def disponible(self) -> tuple[bool, str]:
        if not self.definicion.get("habilitado", False):
            return False, "El verificador en el servidor no está habilitado (falta la validación del servidor y del dueño)."
        if not self.url_base or not self.modelo:
            return False, "Faltan la dirección o el modelo de Ollama en perfiles/pc.local.toml."
        try:
            with urllib.request.urlopen(f"{self.url_base}/api/tags", timeout=5) as r:
                modelos = [m.get("name", "") for m in json.loads(r.read().decode("utf-8")).get("models", [])]
        except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError) as e:
            return False, f"El servidor del verificador no responde: {getattr(e, 'reason', e)}"
        if not any(m == self.modelo or m.split(":")[0] == self.modelo for m in modelos):
            return False, f"El servidor no tiene el modelo «{self.modelo}»."
        return True, ""

    def _llamar(self, prompt: str) -> tuple[str, str]:
        ok, motivo = self.cabe(prompt)
        if not ok:
            raise AdaptadorError(motivo)
        cuerpo = {"model": self.modelo, "stream": False, "format": "json",
                  "messages": [{"role": "user", "content": prompt}],
                  "options": {"num_predict": self.num_predict}}
        datos = _post_json(f"{self.url_base}/api/chat", cuerpo, {}, self.tiempo_maximo)
        texto = (datos.get("message") or {}).get("content", "")
        if not texto:
            raise AdaptadorError(f"Ollama no devolvió texto: {str(datos)[:300]}")
        # Detección de recorte: entrada truncada por el contexto o salida cortada por num_predict.
        evaluados = datos.get("prompt_eval_count")
        if isinstance(evaluados, int):
            if evaluados >= self.contexto - 16 or evaluados < estimar_tokens(prompt) * 0.5:
                raise AdaptadorError(
                    f"Ollama recortó el prompt (evaluó {evaluados} tokens de ≈{estimar_tokens(prompt)}). Se descarta la respuesta.")
        if datos.get("done_reason") == "length":
            raise AdaptadorError("La respuesta de Ollama se cortó por longitud. Se descarta.")
        return texto, json.dumps(datos, ensure_ascii=False)
