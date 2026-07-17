#!/usr/bin/env python3
"""Generic glTF catalog: thumbs, videos, and a browsable viewer.

Env vars:
  GLTF_DIR       root of models, glob is $GLTF_DIR/*/*.gltf  (default: gltf)
  CATALOG_DIR    output root                                  (default: .catalog/gltf)
  PAGE_SIZE      grid page size for `serve`                   (default: 6)
  GLTF_TO_PNG    renderer bin for thumbs   (required for gen-thumbs)
  GLTF_TO_WEBM   renderer bin for videos   (required for gen-videos)
  NO_GPU=1       force software EGL + xvfb-run wrapping
  XVFB_RUN       path to xvfb-run (required if NO_GPU or no /dev/dri/renderD*)

Layout expected: $GLTF_DIR/<Name.gltf>/<Name.gltf>
Outputs:
  $CATALOG_DIR/thumbs/<Name.gltf>.png
  $CATALOG_DIR/video/<Name.gltf>.webm
"""
import os, sys, glob, json, shutil, socketserver, http.server, subprocess, webbrowser
from pathlib import Path

GLTF_DIR = os.environ.get("GLTF_DIR", "gltf")
CATALOG_DIR = os.environ.get("CATALOG_DIR", ".catalog/gltf")
VIEWERS_DIR = Path(__file__).resolve().parent / "viewers"


def _models():
    return sorted(glob.glob(f"{GLTF_DIR}/*/*.gltf"))


def _needs_xvfb():
    if os.environ.get("NO_GPU") == "1":
        return True
    return not glob.glob("/dev/dri/renderD*")


def _wrapper():
    if not _needs_xvfb():
        return []
    xvfb = os.environ.get("XVFB_RUN") or shutil.which("xvfb-run")
    if not xvfb:
        print("WARNING: xvfb-run not found, running renderer directly", file=sys.stderr)
        return []
    os.environ.setdefault("EGL_PLATFORM", "surfaceless")
    os.environ.setdefault("GALLIUM_DRIVER", "softpipe")
    return [xvfb, "-a"]


def _render_loop(kind, bin_env, out_ext, out_subdir):
    bin_path = os.environ.get(bin_env)
    if not bin_path:
        sys.exit(f"{bin_env} not set")
    out_root = Path(CATALOG_DIR) / out_subdir
    out_root.mkdir(parents=True, exist_ok=True)
    wrapper = _wrapper()
    print(f"=== Generating {kind} ===")
    for gltf in _models():
        name = Path(gltf).parent.name  # e.g. Aemis.gltf
        out = out_root / f"{name}.{out_ext}"
        if out.exists():
            print(f"==> {out.name} (exists, skipping)")
            continue
        print(f"==> {out.name}")
        rc = subprocess.call(wrapper + [bin_path, "-i", gltf, "-o", str(out)])
        if rc != 0:
            crash = Path("/tmp/blender.crash.txt")
            if crash.exists():
                sys.stdout.write(crash.read_text())


def cmd_gen_thumbs():
    _render_loop("thumbnails", "GLTF_TO_PNG", "png", "thumbs")


def cmd_gen_videos():
    _render_loop("videos", "GLTF_TO_WEBM", "webm", "video")


def _open_private(url):
    for exe, flag in [("firefox", "--private-window"),
                      ("chromium", "--incognito"),
                      ("google-chrome", "--incognito")]:
        path = shutil.which(exe)
        if path:
            subprocess.Popen([path, flag, url],
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return
    webbrowser.open(url)


def cmd_serve():
    models = _models()
    if not models:
        sys.exit(f"No .gltf files found in {GLTF_DIR}/*/")
    # URL paths served relative to $SRC; folder basename kept intact.
    paths = [f"/{GLTF_DIR}/{Path(m).parent.name}/{Path(m).name}" for m in models]
    page_size = os.environ.get("PAGE_SIZE", "6")
    src = os.getcwd()
    # Symlink viewers/ into a temp-served path — but simpler: serve from $SRC
    # and route /_viewers/ to the packaged viewers dir.
    viewers = VIEWERS_DIR
    files_json = json.dumps(paths).encode()

    class Handler(http.server.SimpleHTTPRequestHandler):
        def do_GET(self):
            # The full model list is fetched here, not shoved into the URL —
            # keeps the launch URL tiny so the catalog size is unbounded.
            if self.path.split("?", 1)[0] == "/_files.json":
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(files_json)))
                self.end_headers()
                self.wfile.write(files_json)
                return
            return super().do_GET()

        def translate_path(self, path):
            # Route /_viewers/foo -> packaged viewers dir
            if path.startswith("/_viewers/"):
                rel = path[len("/_viewers/"):].split("?", 1)[0].split("#", 1)[0]
                return str(viewers / rel)
            return super().translate_path(path)

    os.chdir(src)
    with socketserver.TCPServer(("127.0.0.1", 0), Handler) as httpd:
        port = httpd.server_address[1]
        url = (f"http://127.0.0.1:{port}/_viewers/grid_viewer.html"
               f"?page_size={page_size}")
        print(f"Serving {src}")
        print(f"Opening {len(paths)} models ({page_size} per page)")
        print(f"URL: {url}")
        _open_private(url)
        httpd.serve_forever()


CMDS = {
    "serve": cmd_serve,
    "gen-thumbs": cmd_gen_thumbs,
    "gen-videos": cmd_gen_videos,
}


def main():
    if len(sys.argv) < 2 or sys.argv[1] not in CMDS:
        sys.exit(f"usage: gltf_catalog.py {{{'|'.join(CMDS)}}}")
    CMDS[sys.argv[1]]()


if __name__ == "__main__":
    main()
