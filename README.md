# gltf_catalog

Browsable web viewer + thumbnail/video generator for a directory of `.gltf` models.

Expected layout: `$GLTF_DIR/<Name.gltf>/<Name.gltf>`

## Use as a flake input

```nix
{
  inputs.gltf_catalog.url = "github:M4jor-Tom/gltf_catalog.py";

  outputs = { self, nixpkgs, gltf_catalog, ... }: {
    apps.x86_64-linux = gltf_catalog.lib.x86_64-linux.mkApps {
      gltfDir = "/abs/path/to/models";       # optional, default: ./gltf
      catalogDir = "/abs/path/to/.catalog";  # optional, default: ./.catalog/gltf
    };
  };
}
```

Then:

```sh
nix run .#serve        # browse the catalog in your browser
nix run .#gen-thumbs   # (re)generate PNG thumbnails
nix run .#gen-videos   # (re)generate WebM previews
```

`mkApps { }` with no args behaves like the flake's own `apps` output: paths are
resolved relative to the current working directory.

## Run directly (no wrapper flake)

```sh
GLTF_DIR=/abs/path/to/models nix run github:M4jor-Tom/gltf_catalog.py#serve
```

## Env vars

| Var           | Default          | Purpose                                   |
|---------------|------------------|-------------------------------------------|
| `GLTF_DIR`    | `gltf`           | model root, globbed as `$GLTF_DIR/*/*.gltf` |
| `CATALOG_DIR` | `.catalog/gltf`  | output root for thumbs/videos             |
| `PAGE_SIZE`   | `6`              | grid page size for `serve`                |
| `NO_GPU=1`    | unset            | force software EGL + `xvfb-run`           |

Outputs land in `$CATALOG_DIR/thumbs/<Name.gltf>.png` and
`$CATALOG_DIR/video/<Name.gltf>.webm`.
