{ pkgs ? import <nixpkgs> { } }:

let
  pythonEnv = pkgs.python3.withPackages (ps: with ps; [ ]);
in
pkgs.mkShell {
  packages = [
    pythonEnv
    pkgs.openldap
    pkgs.cyrus_sasl
    pkgs.mongosh
  ];
  shellHook = ''
    source .venv/bin/activate 
    set -a
    source .env 
    set +a
    export UID=$(id -u) 
    export GID=$(id -g)
  '';
}
