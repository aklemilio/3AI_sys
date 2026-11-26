"""python -m tresia.interfaz [--carpeta ejecuciones] [--puerto 8765] [--perfil pc] [--abrir]"""

from __future__ import annotations

import argparse
import webbrowser
from pathlib import Path

from tresia import RAIZ, perfiles
from tresia.interfaz.servidor import Aplicacion, crear_servidor
from tresia.motor.llamadas import Recursos


def main() -> None:
    p = argparse.ArgumentParser(description="Interfaz local del sistema de tres IA (solo 127.0.0.1).")
    p.add_argument("--carpeta", default=str(RAIZ / "ejecuciones"), help="Dónde se guardan las ejecuciones.")
    p.add_argument("--puerto", type=int, default=8765)
    p.add_argument("--perfil", default="pc")
    p.add_argument("--abrir", action="store_true", help="Abrir el navegador al arrancar.")
    args = p.parse_args()

    perfil, recursos, motivo = None, None, ""
    try:
        perfil = perfiles.cargar(args.perfil)
        recursos = Recursos.desde_perfil(perfil)
    except Exception as e:  # sin perfil la herramienta funciona en modo manual
        motivo = f"No se pudo cargar el perfil «{args.perfil}»: {e}"

    app = Aplicacion(Path(args.carpeta), perfil, recursos, motivo)
    servidor = crear_servidor(app, args.puerto)
    url = f"http://127.0.0.1:{app.puerto}/"
    print(f"Interfaz en {url}  (Ctrl+C para cerrar)")
    if motivo:
        print(motivo + " Todo irá en modo manual.")
    if args.abrir:
        webbrowser.open(url)
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        print("\nCerrada.")
    finally:
        servidor.server_close()


if __name__ == "__main__":
    main()
