import json
import threading
import time
import websocket
from whisper_live.client import TranscriptionClient
import argparse
import hashlib
import base64


class WhisperToOBSBridge:
    """
    WhisperLive の出力を OBS Studio テキストソースに流し込むブリッジ
    OBS WebSocket v5 に対応（認証対応）
    """
    
    def __init__(self, obs_host='localhost', obs_port=4444, obs_password=None, 
                 text_source_name='TranscribedText', max_words=None):
        """
        Args:
            obs_host: OBS WebSocket サーバーのホスト名
            obs_port: OBS WebSocket サーバーのポート番号
            obs_password: OBS WebSocket サーバーのパスワード（必要に応じて）
            text_source_name: テキストを書き込む OBS テキストソースの名前
            max_words: 表示する最大語数（デフォルト: 全て表示）
        """
        self.obs_host = obs_host
        self.obs_port = obs_port
        self.obs_password = obs_password
        self.text_source_name = text_source_name
        self.max_words = max_words
        self.obs_ws = None
        self.connect_lock = threading.Lock()
        self.request_id = 0
        self.identified = False
        self.challenge = None
        self.salt = None
        self.connect_to_obs()
        
    def get_request_id(self):
        """リクエストID を生成"""
        self.request_id += 1
        return str(self.request_id)
    
    def truncate_text(self, text):
        """テキストを最大語数で切り詰める"""
        if self.max_words is None:
            return text
        
        words = text.split()
        if len(words) > self.max_words:
            truncated = ' '.join(words[-self.max_words:])
            return truncated + '...'
        return text
    
    def connect_to_obs(self):
        """OBS WebSocket サーバーに接続"""
        try:
            print(f"[INFO]: OBS WebSocket に接続中... ({self.obs_host}:{self.obs_port})")
            
            # WebSocket に接続
            url = f"ws://{self.obs_host}:{self.obs_port}"
            self.obs_ws = websocket.WebSocketApp(
                url,
                on_open=self.on_open,
                on_message=self.on_message,
                on_error=self.on_error,
                on_close=self.on_close
            )
            
            # WebSocket を別スレッドで実行
            self.ws_thread = threading.Thread(target=self.obs_ws.run_forever, daemon=True)
            self.ws_thread.start()
            
            # 接続と認証を待つ
            for _ in range(50):  # 最大5秒待機
                if self.identified:
                    print(f"[INFO]: OBS WebSocket に認証済みで接続しました")
                    if self.max_words:
                        print(f"[INFO]: 表示する最大語数: {self.max_words}")
                    return
                time.sleep(0.1)
            
            if not self.identified:
                print("[INFO]: OBS WebSocket に接続しました（認証なし）")
                if self.max_words:
                    print(f"[INFO]: 表示する最大語数: {self.max_words}")
                self.identified = True  # 認証なしでも続行
            
        except Exception as e:
            print(f"[ERROR]: OBS WebSocket への接続に失敗しました: {e}")
            self.obs_ws = None
            raise
    
    def on_open(self, ws):
        """WebSocket 接続時のコールバック"""
        print("[DEBUG]: WebSocket 接続を開きました")
    
    def on_message(self, ws, message):
        """メッセージ受信時のコールバック"""
        try:
            data = json.loads(message)
            op = data.get('op')
            
            if op == 0:  # Hello
                print("[DEBUG]: Hello メッセージを受信")
                auth_data = data.get('d', {})
                self.challenge = auth_data.get('challenge')
                self.salt = auth_data.get('salt')
                self.identify(auth_data)
                
            elif op == 1:  # Identified
                print("[DEBUG]: Identified - 認証成功")
                self.identified = True
                
            elif op == 7:  # RequestResponse
                request_status = data.get('d', {}).get('requestStatus', {})
                result = request_status.get('result', True)
                code = request_status.get('code', 0)
                if not result:
                    print(f"[DEBUG]: リクエスト失敗 - コード: {code}, メッセージ: {request_status.get('comment', 'Unknown')}")
                
        except Exception as e:
            print(f"[DEBUG]: メッセージ処理エラー: {e}")
    
    def on_error(self, ws, error):
        """エラー時のコールバック"""
        print(f"[ERROR]: WebSocket エラー: {error}")
    
    def on_close(self, ws, close_status_code, close_msg):
        """接続切断時のコールバック"""
        print(f"[INFO]: WebSocket 接続を閉じました")
        self.identified = False
    
    def identify(self, auth_data):
        """OBS WebSocket v5 認証"""
        try:
            request = {
                "op": 1,  # Identify opcode
                "d": {
                    "rpcVersion": 1
                }
            }
            
            # パスワードが設定されている場合、認証情報を追加
            if self.obs_password:
                challenge = auth_data.get('challenge')
                salt = auth_data.get('salt')
                
                if challenge and salt:
                    print(f"[DEBUG]: パスワード認証を実行します")
                    # OBS WebSocket v5 認証方式
                    secret_string = self.obs_password + salt
                    secret = hashlib.sha256(secret_string.encode()).digest()
                    secret_b64 = base64.b64encode(secret).decode()
                    
                    auth_string = secret_b64 + challenge
                    auth_hash = base64.b64encode(hashlib.sha256(auth_string.encode()).digest()).decode()
                    
                    request["d"]["authentication"] = auth_hash
            else:
                print(f"[DEBUG]: パスワードが設定されていません")
            
            message = json.dumps(request)
            self.obs_ws.send(message)
            print("[DEBUG]: Identify リクエストを送信しました")
            
            # 認証なしの場合も続行
            if not self.obs_password:
                time.sleep(0.2)
                self.identified = True
            
        except Exception as e:
            print(f"[ERROR]: 認証エラー: {e}")
            self.identified = True  # エラーでも続行
    
    def send_request(self, request_type, request_data):
        """OBS WebSocket v5 形式でリクエストを送信"""
        if not self.obs_ws or not self.obs_ws.sock:
            return False
        
        if not self.identified:
            print("[WARN]: OBS WebSocket がまだ認証されていません")
            return False
        
        try:
            with self.connect_lock:
                # OBS WebSocket v5 形式のリクエスト
                request = {
                    "op": 6,  # Request opcode
                    "d": {
                        "requestType": request_type,
                        "requestId": self.get_request_id(),
                        "requestData": request_data
                    }
                }
                
                message = json.dumps(request)
                self.obs_ws.send(message)
                return True
                
        except Exception as e:
            print(f"[WARN]: OBS リクエスト送信エラー: {e}")
            return False
    
    def update_text_source(self, text):
        """OBS のテキストソースを更新"""
        if not self.obs_ws or not self.obs_ws.sock:
            return
        
        try:
            # テキストを切り詰める
            display_text = self.truncate_text(text)
            
            # SetInputSettings リクエストを送信
            request_data = {
                "inputName": self.text_source_name,
                "inputSettings": {
                    "text": display_text
                }
            }
            
            success = self.send_request("SetInputSettings", request_data)
            if success:
                print(f"[OBS UPDATE]: {display_text[:60]}...")
            
        except Exception as e:
            print(f"[WARN]: OBS テキスト更新エラー: {e}")
    
    def transcription_callback(self, text, segments):
        """
        WhisperLive の文字起こしコールバック
        テキストを OBS に送信
        
        Args:
            text: 文字起こし結果のテキスト
            segments: セグメント情報のリスト
        """
        print(f"[TRANSCRIPTION]: {text}")
        self.update_text_source(text)
    
    def close(self):
        """OBS WebSocket 接続を切断"""
        if self.obs_ws:
            try:
                self.obs_ws.close()
                print("[INFO]: OBS WebSocket から切断しました")
            except Exception as e:
                print(f"[DEBUG]: OBS WebSocket 切断時のエラー: {e}")


def main():
    parser = argparse.ArgumentParser(
        description='WhisperLive の出力を OBS Studio テキストソースに流し込む'
    )
    
    # Whisper Server オプション
    parser.add_argument('--server', '-s',
                        type=str,
                        default='localhost',
                        help='WhisperLive サーバーのホスト名またはIP')
    parser.add_argument('--port', '-p',
                        type=int,
                        default=9090,
                        help='WhisperLive サーバーのポート番号')
    
    # OBS オプション
    parser.add_argument('--obs-host',
                        type=str,
                        default='localhost',
                        help='OBS WebSocket サーバーのホスト名 (デフォルト: localhost)')
    parser.add_argument('--obs-port',
                        type=int,
                        default=4444,
                        help='OBS WebSocket サーバーのポート番号 (デフォルト: 4444)')
    parser.add_argument('--obs-password',
                        type=str,
                        default=None,
                        help='OBS WebSocket サーバーのパスワード')
    parser.add_argument('--obs-text-source',
                        type=str,
                        default='TranscribedText',
                        help='OBS テキストソースの名前 (デフォルト: TranscribedText)')
    parser.add_argument('--max-words',
                        type=int,
                        default=None,
                        help='表示する最大語数（デフォルト: 全て表示）')
    
    # Whisper オプション
    parser.add_argument('--model', '-m',
                        type=str,
                        default='small',
                        help='使用する Whisper モデル')
    parser.add_argument('--lang', '-l',
                        type=str,
                        default='en',
                        help='文字起こしの言語コード')
    parser.add_argument('--translate', '-t',
                        action='store_true',
                        help='Whisper の組み込み翻訳を使用 (英語に翻訳)')
    
    args = parser.parse_args()
    
    try:
        # OBS ブリッジの初期化
        obs_bridge = WhisperToOBSBridge(
            obs_host=args.obs_host,
            obs_port=args.obs_port,
            obs_password=args.obs_password,
            text_source_name=args.obs_text_source,
            max_words=args.max_words
        )
        
        # WhisperLive クライアントの初期化
        client = TranscriptionClient(
            args.server,
            args.port,
            lang=args.lang,
            translate=args.translate,
            model=args.model,
            use_vad=True,
            transcription_callback=obs_bridge.transcription_callback,
            log_transcription=True,  # コンソール出力も有効
        )
        
        print("[INFO]: マイクからの文字起こしを開始します...")
        print(f"[INFO]: OBS テキストソース '{args.obs_text_source}' に結果を送信中...")
        print("[INFO]: Ctrl+C で停止できます")
        
        # 文字起こしの実行（マイク入力）
        client()
        
    except KeyboardInterrupt:
        print("\n[INFO]: ユーザーによる中断")
    except Exception as e:
        print(f"[ERROR]: エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if 'obs_bridge' in locals():
            obs_bridge.close()
        print("[INFO]: 終了しました")


if __name__ == '__main__':
    main()
