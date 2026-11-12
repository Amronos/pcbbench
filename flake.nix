{
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs =
    { nixpkgs, flake-utils, ... }:
    flake-utils.lib.eachDefaultSystem (
      system:
      let
        pkgs = import nixpkgs {
          inherit system;
          # gerbv still needs gtk2, which nixpkgs marks broken ahead of removing it.
          config.problems.handlers."gtk+".broken = "ignore";
        };
      in
      {
        formatter = pkgs.nixfmt-tree;

        devShells.default = pkgs.mkShell {
          packages = with pkgs; [
            awscli2
            bun
            commitlint
            gerbv
            imagemagick
            librsvg
            nodejs_26
            prek
            unzip
          ];
        };
      }
    );
}
