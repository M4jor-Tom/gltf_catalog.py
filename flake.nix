{
  description = "Generic glTF catalog: thumbs, videos, and a browsable web viewer.";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    gltf_to_png.url = "github:M4jor-Tom/gltf_to_png.py";
    gltf_to_webm.url = "github:M4jor-Tom/gltf_to_webm.py";
  };

  outputs = { self, nixpkgs, gltf_to_png, gltf_to_webm }:
    let
      systems = [ "x86_64-linux" "aarch64-linux" "x86_64-darwin" "aarch64-darwin" ];
      forAllSystems = nixpkgs.lib.genAttrs systems;

      mkAppsFor = system: { gltfDir ? null, catalogDir ? null, extraEnv ? "" }:
        let
          pkgs = import nixpkgs { inherit system; };
          py = pkgs.python3;
          catalogRoot = ./.;
          png = gltf_to_png.apps.${system}.default.program;
          webm = gltf_to_webm.apps.${system}.default.program;
          exports = nixpkgs.lib.concatStringsSep "\n" (nixpkgs.lib.optional (gltfDir != null) ''export GLTF_DIR="${toString gltfDir}"''
            ++ nixpkgs.lib.optional (catalogDir != null) ''export CATALOG_DIR="${toString catalogDir}"'');
          mkApp = name: {
            type = "app";
            program = "${pkgs.writeShellScriptBin "gltf-catalog-${name}" ''
              export GLTF_TO_PNG="${png}"
              export GLTF_TO_WEBM="${webm}"
              export XVFB_RUN="${pkgs.xvfb-run}/bin/xvfb-run"
              ${exports}
              ${extraEnv}
              exec ${py}/bin/python3 ${catalogRoot}/gltf_catalog.py ${name} "$@"
            ''}/bin/gltf-catalog-${name}";
          };
        in {
          serve      = mkApp "serve";
          gen-thumbs = mkApp "gen-thumbs";
          gen-videos = mkApp "gen-videos";
          default    = mkApp "serve";
        };
    in {
      lib = forAllSystems (system: { mkApps = mkAppsFor system; });
      apps = forAllSystems (system: mkAppsFor system {});
    };
}
