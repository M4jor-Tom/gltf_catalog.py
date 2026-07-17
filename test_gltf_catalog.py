#!/usr/bin/env python3
"""Self-check for serve path routing. Run: python test_gltf_catalog.py"""
import tempfile, os
from pathlib import Path
import gltf_catalog as g


def test_out_of_tree_model_resolves():
    # Models live OUTSIDE the server CWD — the case that used to 404.
    with tempfile.TemporaryDirectory() as models, tempfile.TemporaryDirectory() as catalog:
        asset = Path(models) / "Foo.gltf" / "Foo.gltf"
        asset.parent.mkdir(parents=True)
        asset.write_text("{}")
        routes = {"/_models/": Path(models), "/_catalog/": Path(catalog)}
        resolved = g._resolve_route("/_models/Foo.gltf/Foo.gltf", routes)
        assert resolved is not None, "route did not match"
        assert Path(resolved) == asset, f"{resolved} != {asset}"
        assert Path(resolved).exists(), "resolved to a non-existent path"


def test_query_and_fragment_stripped():
    routes = {"/_models/": Path("/srv/models")}
    assert g._resolve_route("/_models/a/b.gltf?x=1#y", routes) == str(Path("/srv/models/a/b.gltf"))


def test_unmatched_prefix_falls_through():
    assert g._resolve_route("/favicon.ico", {"/_models/": Path("/srv")}) is None


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn(); print(f"ok  {name}")
    print("all passed")
