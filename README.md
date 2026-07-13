<!-- Japanese Version -->

# WhisperLive OBS Integration

リアルタイム音声認識を OBS Studio に統合するツール

## 概要

このプロジェクトは、WhisperLive サーバーからのリアルタイム音声認識結果を OBS Studio のテキストソースに自動的に流し込みます。ライブストリーミングやビデオ制作時に、リアルタイムで文字起こしを画面に表示できます。

## 機能

- 🎤 **リアルタイム音声認識** - マイク入力からリアルタイムで音声を認識
- 🎬 **OBS 統合** - 認識結果を OBS のテキストソースに自動更新
- 🌍 **多言語対応** - 複数の言語をサポート
- 📝 **表示語数制限** - 画面に表示する最大語数を指定可能
- 🔒 **OBS 認証対応** - パスワード保護されたOBS WebSocket に対応

---

## インストール

### 前提条件

- Python 3.8 以上
- マイク
- OBS Studio 28.0 以上
- WhisperLive サーバーが起動している

### ステップ1: リポジトリをクローン

```bash
git clone https://github.com/ergodice/WhisperLive-obs.git
cd WhisperLive-obs
```

### ステップ2: 依存関係をインストール

```bash
pip install -r requirements/obs_source.txt
pip install whisper-live-client
```

> **注**: `whisper-live-client` は別途インストールが必要です。

### ステップ3: OBS Studio の設定

#### 3-1. WebSocket Server を有効化

1. OBS Studio を開く
2. **Tools** → **WebSocket Server Settings** を選択
3. **Enable WebSocket Server** にチェックを入れる
4. ポート番号を確認（デフォルト: 4444）
5. 必要に応じてパスワードを設定

#### 3-2. テキストソースを作成

1. **Sources** で **+** をクリック
2. **Text (GDI+)** または **Text (Freetype 2)** を選択
3. ソース名を **TranscribedText** と設定（またはカスタム名）
4. OKをクリック

---

## 使い方

### 基本的な実行

```bash
python run_client_obs.py
```

デフォルト設定：
- WhisperLive サーバー: `localhost:9090`
- OBS WebSocket: `localhost:4444`
- テキストソース名: `TranscribedText`
- 言語: 英語 (`en`)

### 実行例

#### 例1: 日本語で認識

```bash
python run_client_obs.py --lang ja
```

#### 例2: OBS パスワード付き

```bash
python run_client_obs.py --obs-password your_password
```

#### 例3: 最新の10語だけを表示

```bash
python run_client_obs.py --max-words 10
```

#### 例4: リモートサーバーに接続

```bash
python run_client_obs.py --server 192.168.1.100 --port 9090
```

#### 例5: 複数オプション組み合わせ

```bash
python run_client_obs.py \
    --server 192.168.1.100 \
    --port 9090 \
    --lang ja \
    --obs-port 4455 \
    --obs-password secret_pass \
    --obs-text-source "Transcription" \
    --max-words 20
```

---

## コマンドラインオプション

### WhisperLive サーバーオプション

| オプション | 短形 | デフォルト | 説明 |
|-----------|------|----------|------|
| `--server` | `-s` | `localhost` | WhisperLive サーバーのホスト名またはIP |
| `--port` | `-p` | `9090` | WhisperLive サーバーのポート番号 |

### OBS オプション

| オプション | デフォルト | 説明 |
|-----------|----------|------|
| `--obs-host` | `localhost` | OBS WebSocket サーバーのホスト名 |
| `--obs-port` | `4444` | OBS WebSocket サーバーのポート番号 |
| `--obs-password` | なし | OBS WebSocket サーバーのパスワード |
| `--obs-text-source` | `TranscribedText` | OBS テキストソースの名前 |
| `--max-words` | なし | 表示する最大語数（指定しない場合は全て表示） |

### 音声認識オプション

| オプション | 短形 | デフォルト | 説明 |
|-----------|------|----------|------|
| `--model` | `-m` | `small` | 使用する Whisper モデル (`tiny`, `base`, `small`, `medium`, `large`) |
| `--lang` | `-l` | `en` | 言語コード (`en`, `ja`, `fr`, `de` など) |
| `--translate` | `-t` | - | 翻訳機能を有効化（英語に翻訳） |

---

## WhisperLive サーバーの起動

別のターミナルで WhisperLive サーバーを起動してください。

### Docker を使用する場合（推奨）

```bash
docker run -it -p 9090:9090 ghcr.io/collabora/whisper-live:latest
```

### ローカルで起動

```bash
whisper-live-server --host 0.0.0.0 --port 9090
```

接続時間を2時間に設定する場合：

```bash
whisper-live-server --host 0.0.0.0 --port 9090 --max-connection-time 7200
```

---

## トラブルシューティング

### OBS に接続できない

1. OBS の WebSocket Server が有効になっているか確認
   - Tools → WebSocket Server Settings を開く
   - "Enable WebSocket Server" にチェック

2. ポート番号が正しいか確認
   - デフォルト: 4444 (OBS 28+)
   - 古いバージョンでは異なる場合があります

3. ファイアウォール設定を確認

### マイクが認識されない

```bash
python -c "import pyaudio; p = pyaudio.PyAudio(); print(p.get_device_count())"
```

### テキストが表示されない

1. OBS テキストソース名が正確に一致しているか確認
2. テキストソースがシーンに配置されているか確認
3. テキストソースのテキストコンテンツを確認

---

## 言語コード参考表

| 言語 | コード | 言語 | コード |
|------|------|------|------|
| 英語 | `en` | 日本語 | `ja` |
| スペイン語 | `es` | 中国語 | `zh` |
| フランス語 | `fr` | 韓国語 | `ko` |
| ドイツ語 | `de` | ポルトガル語 | `pt` |

[全言語一覧](https://github.com/openai/whisper#available-models-and-languages)

---

## ライセンス

MIT License

## 関連リンク

- [WhisperLive GitHub](https://github.com/collabora/WhisperLive)
- [OBS Studio](https://obsproject.com/)
- [OpenAI Whisper](https://github.com/openai/whisper)

---

---

<!-- English Version -->

# WhisperLive OBS Integration

Real-time speech recognition integration for OBS Studio

## Overview

This project automatically streams real-time speech recognition results from WhisperLive server to OBS Studio text sources. Perfect for live streaming and video production where you want live captions displayed on screen.

## Features

- 🎤 **Real-time Speech Recognition** - Recognize speech from microphone input in real-time
- 🎬 **OBS Integration** - Automatically update OBS text sources with recognition results
- 🌍 **Multi-language Support** - Support for multiple languages
- 📝 **Display Word Limit** - Specify maximum number of words to display on screen
- 🔒 **OBS Authentication** - Support for password-protected OBS WebSocket

---

## Installation

### Prerequisites

- Python 3.8 or higher
- Microphone
- OBS Studio 28.0 or later
- WhisperLive server running

### Step 1: Clone the Repository

```bash
git clone https://github.com/ergodice/WhisperLive-obs.git
cd WhisperLive-obs
```

### Step 2: Install Dependencies

```bash
pip install -r requirements/obs_source.txt
pip install whisper-live-client
```

> **Note**: `whisper-live-client` needs to be installed separately.

### Step 3: Configure OBS Studio

#### 3-1. Enable WebSocket Server

1. Open OBS Studio
2. Go to **Tools** → **WebSocket Server Settings**
3. Check **Enable WebSocket Server**
4. Note the port number (default: 4444)
5. Optionally set a password

#### 3-2. Create Text Source

1. Click **+** in **Sources**
2. Select **Text (GDI+)** or **Text (Freetype 2)**
3. Set the source name to **TranscribedText** (or custom name)
4. Click OK

---

## Usage

### Basic Usage

```bash
python run_client_obs.py
```

Default settings:
- WhisperLive server: `localhost:9090`
- OBS WebSocket: `localhost:4444`
- Text source name: `TranscribedText`
- Language: English (`en`)

### Examples

#### Example 1: Japanese Language

```bash
python run_client_obs.py --lang ja
```

#### Example 2: With OBS Password

```bash
python run_client_obs.py --obs-password your_password
```

#### Example 3: Display Only Last 10 Words

```bash
python run_client_obs.py --max-words 10
```

#### Example 4: Connect to Remote Server

```bash
python run_client_obs.py --server 192.168.1.100 --port 9090
```

#### Example 5: Combined Options

```bash
python run_client_obs.py \
    --server 192.168.1.100 \
    --port 9090 \
    --lang ja \
    --obs-port 4455 \
    --obs-password secret_pass \
    --obs-text-source "Transcription" \
    --max-words 20
```

---

## Command-line Options

### WhisperLive Server Options

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--server` | `-s` | `localhost` | WhisperLive server hostname or IP address |
| `--port` | `-p` | `9090` | WhisperLive server port number |

### OBS Options

| Option | Default | Description |
|--------|---------|-------------|
| `--obs-host` | `localhost` | OBS WebSocket server hostname |
| `--obs-port` | `4444` | OBS WebSocket server port number |
| `--obs-password` | None | OBS WebSocket server password |
| `--obs-text-source` | `TranscribedText` | OBS text source name |
| `--max-words` | None | Maximum words to display (shows all if not specified) |

### Speech Recognition Options

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--model` | `-m` | `small` | Whisper model to use (`tiny`, `base`, `small`, `medium`, `large`) |
| `--lang` | `-l` | `en` | Language code (`en`, `ja`, `fr`, `de`, etc.) |
| `--translate` | `-t` | - | Enable translation (to English) |

---

## Running WhisperLive Server

Start the WhisperLive server in a separate terminal.

### Using Docker (Recommended)

```bash
docker run -it -p 9090:9090 ghcr.io/collabora/whisper-live:latest
```

### Local Installation

```bash
whisper-live-server --host 0.0.0.0 --port 9090
```

To set maximum connection time to 2 hours:

```bash
whisper-live-server --host 0.0.0.0 --port 9090 --max-connection-time 7200
```

---

## Troubleshooting

### Cannot Connect to OBS

1. Verify WebSocket Server is enabled in OBS
   - Tools → WebSocket Server Settings
   - Check "Enable WebSocket Server"

2. Verify correct port number
   - Default: 4444 (OBS 28+)
   - May differ on older versions

3. Check firewall settings

### Microphone Not Recognized

```bash
python -c "import pyaudio; p = pyaudio.PyAudio(); print(p.get_device_count())"
```

### Text Not Displaying

1. Verify OBS text source name matches exactly
2. Verify text source is placed in the scene
3. Check text source content settings

---

## Language Codes Reference

| Language | Code | Language | Code |
|----------|------|----------|------|
| English | `en` | Japanese | `ja` |
| Spanish | `es` | Chinese | `zh` |
| French | `fr` | Korean | `ko` |
| German | `de` | Portuguese | `pt` |

[Full language list](https://github.com/openai/whisper#available-models-and-languages)

---

## License

MIT License

## Related Links

- [WhisperLive GitHub](https://github.com/collabora/WhisperLive)
- [OBS Studio](https://obsproject.com/)
- [OpenAI Whisper](https://github.com/openai/whisper)
