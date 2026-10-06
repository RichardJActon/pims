{ pkgs ? import (fetchTarball {
  url = "https://github.com/NixOS/nixpkgs/archive/refs/tags/26.05.tar.gz";
  sha256 = "sha256-md0zn0RnwNvPyASas1yG5YUuwQ4ALA6ucL50l0DvqCo=";
}) { } }:

let
  pythonEnv = pkgs.python3.withPackages (ps: with ps; [ ]);
in
pkgs.mkShell {
  packages = [
    pythonEnv
    pkgs.openldap
    pkgs.cyrus_sasl
    pkgs.mongosh
    pkgs.mongodb
    pkgs.openldap
    pkgs.psmisc
    pkgs.nodejs_26
  ];
  shellHook = ''
    source .venv/bin/activate 
    set -a
    source .env 
    set +a
    # export UID=$(id -u) 
    # export GID=$(id -g)
  '';
}
