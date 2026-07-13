{
  description = "Whisper-Live development environment";

  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs/nixos-unstable";
  };

  outputs = { self, nixpkgs }:
    let
      system = "x86_64-linux";
      pkgs = import nixpkgs { inherit system; };
    in {
      devShells.${system}.default = pkgs.mkShell {
        name = "whisper-live-shell";

        buildInputs = with pkgs; [
          python313
          portaudio
          ffmpeg-full
          gcc
          ninja    # 追加: ビルドツール
          meson    # 追加: ビルドシステム
          pkg-config # 追加: ライブラリのパス解決に必要
          stdenv.cc.cc.lib
        ];

        shellHook = ''
          if [ ! -d ".venv" ]; then
            python3 -m venv .venv
          fi
          source .venv/bin/activate
          pip install --upgrade pip
          
          # Numpyのインストールトラブルを回避するために明示的にセット
          export LD_LIBRARY_PATH="${pkgs.stdenv.cc.cc.lib}/lib:$LD_LIBRARY_PATH"
          
          echo "Environment ready!"
        '';
      };
    };
}
