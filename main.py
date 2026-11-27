import os, json, re, functools, webbrowser, http.server
import urllib.request, urllib.parse

PORT = 8000
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LINKS_PATH = os.path.join(BASE_DIR, "links.txt")
HTML_PATH = os.path.join(BASE_DIR, "index.html")


def actualizar_canciones():
    if not os.path.exists(LINKS_PATH):
        print("No encontré links.txt, se deja el HTML como está.")
        return

    with open(HTML_PATH, encoding="utf-8") as f:
        html = f.read()
    m = re.search(r"<script>window\.CFG\s*=\s*(\{.*?\})\s*</script>", html, re.S)
    if not m:
        raise SystemExit("No encontré window.CFG en index.html")

    # JSON válido aunque el HTML tenga claves sin comillas o comas finales
    texto = re.sub(r",\s*([}\]])", r"\1", m.group(1))
    cfg = json.loads(texto)
    previos = {t["uri"]: t for t in cfg.get("tracks", [])}

    nuevos = []
    with open(LINKS_PATH, encoding="utf-8") as f:
        for linea in f:
            mt = re.search(r"track/([A-Za-z0-9]+)", linea)
            if not mt:
                continue
            uri = f"spotify:track:{mt.group(1)}"
            if uri in previos:                      # conserva título y artista ya escritos
                nuevos.append(previos[uri])
                continue
            url = "https://open.spotify.com/oembed?url=" + urllib.parse.quote(
                f"https://open.spotify.com/track/{mt.group(1)}")
            try:
                titulo = json.load(urllib.request.urlopen(url, timeout=10))["title"]
            except Exception:
                titulo = ""
            nuevos.append({"uri": uri, "title": titulo, "artist": ""})

    if nuevos:
        cfg["tracks"] = nuevos
        script = "<script>window.CFG = " + json.dumps(cfg, ensure_ascii=False, indent=2).replace("</", "<\\/") + "</script>"
        html = html[:m.start()] + script + html[m.end():]
        with open(HTML_PATH, "w", encoding="utf-8") as f:
            f.write(html)
    print(f"{len(nuevos)} canciones en index.html")


if __name__ == "__main__":
    actualizar_canciones()
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=BASE_DIR)
    with http.server.ThreadingHTTPServer(("", PORT), handler) as httpd:
        url = f"http://localhost:{PORT}"
        print(f"Abierto en {url}  (Ctrl+C para detener)")
        webbrowser.open(url)
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServidor detenido")