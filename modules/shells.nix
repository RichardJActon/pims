{
  perSystem = {pkgs, self', ... }: {
    devShells = {
      # default = pkgs.mkShell {
      #   packages = [ self'.packages.mypackage ];  
      # };
      dev = pkgs.mkShellNoCC {
        packages = with pkgs; [
          mongodb
          mongosh
          uv
          openldap
        ];
        shellHook = ''
          ${pkgs.figlet}/bin/figlet $GREETING -f cybermedium
        '';
        # env vars
        GREETING = "PIMS";
      };
    };
  };
}

