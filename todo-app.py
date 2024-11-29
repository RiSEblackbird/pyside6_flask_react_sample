# -*- coding: utf-8 -*-

import sys
import traceback
from pathlib import Path
import threading
import sqlite3
import subprocess
import time
import signal
import os
from flask import Flask, jsonify, request
from flask_cors import CORS
from PySide6.QtWidgets import QApplication, QMainWindow
from PySide6.QtCore import QUrl
from PySide6.QtWebEngineWidgets import QWebEngineView
from datetime import datetime

# 定数定義
DATABASE_PATH = "todo.db"
FLASK_HOST = "127.0.0.1"
FLASK_PORT = 5000
WINDOW_TITLE = "Todoアプリケーション"
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600
FRONTEND_DIR = Path(__file__).parent / "frontend"
VITE_URL = "http://localhost:5173"

def get_exception_trace() -> list:
    """
    概要: 例外のトレースバックを取得
    用途: 例外処理時のデバッグ出力に使用
    """
    t, v, tb = sys.exc_info()
    trace = traceback.format_exception(t, v, tb)
    return trace

class DatabaseManager:
    """
    概要: SQLiteデータベース管理クラス
    用途: Todoデータの永続化を担当
    """
    
    def __init__(self):
        """
        概要: データベース初期化とテーブル作成
        """
        self.init_database()
    
    def init_database(self):
        """
        概要: データベースとテーブルの初期化
        """
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS todos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                completed BOOLEAN NOT NULL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        conn.close()
    
    def get_all_todos(self):
        """
        概要: 全てのTodoアイテムを取得
        """
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM todos ORDER BY created_at DESC')
        todos = cursor.fetchall()
        conn.close()
        return [{'id': t[0], 'title': t[1], 'completed': t[2], 
                 'created_at': t[3]} for t in todos]
    
    def add_todo(self, title):
        """
        概要: 新規Todoの追加
        """
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute('INSERT INTO todos (title) VALUES (?)', (title,))
        todo_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return todo_id
    
    def update_todo(self, todo_id, completed):
        """
        概要: Todo完了状態の更新
        """
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute('UPDATE todos SET completed = ? WHERE id = ?',
                      (completed, todo_id))
        conn.commit()
        conn.close()
    
    def delete_todo(self, todo_id):
        """
        概要: Todoの削除
        """
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM todos WHERE id = ?', (todo_id,))
        conn.commit()
        conn.close()

class ReactDevServer:
    """
    概要: Reactの開発サーバーを管理するクラス
    """
    def __init__(self):
        self.process = None
        
    def start(self):
        """
        概要: React開発サーバーを起動
        """
        os.chdir(FRONTEND_DIR)
        # Windowsの場合はshell=Trueが必要
        self.process = subprocess.Popen(
            "npm run dev",
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        # サーバーの起動を待機
        time.sleep(2)
        os.chdir(Path(__file__).parent)
    
    def stop(self):
        """
        概要: React開発サーバーを停止
        """
        if self.process:
            # Windowsではプロセスツリーごと終了する必要がある
            subprocess.run(f"taskkill /F /T /PID {self.process.pid}", shell=True)

class FlaskAppThread(threading.Thread):
    """
    概要: Flaskアプリケーションをバックグラウンドで実行するスレッド
    用途: PySide6のメインループを妨げないようにFlaskを別スレッドで実行
    """
    
    def __init__(self):
        super().__init__()
        self.flask_app = Flask(__name__)
        CORS(self.flask_app)
        self.db = DatabaseManager()
        self.setup_routes()
    
    def setup_routes(self):
        """
        概要: Flaskルートの設定
        """
        @self.flask_app.route('/api/todos', methods=['GET'])
        def get_todos():
            return jsonify(self.db.get_all_todos())
        
        @self.flask_app.route('/api/todos', methods=['POST'])
        def add_todo():
            data = request.get_json()
            todo_id = self.db.add_todo(data['title'])
            return jsonify({'id': todo_id, 'success': True})
        
        @self.flask_app.route('/api/todos/<int:todo_id>', methods=['PUT'])
        def update_todo(todo_id):
            data = request.get_json()
            self.db.update_todo(todo_id, data['completed'])
            return jsonify({'success': True})
        
        @self.flask_app.route('/api/todos/<int:todo_id>', methods=['DELETE'])
        def delete_todo(todo_id):
            self.db.delete_todo(todo_id)
            return jsonify({'success': True})
    
    def run(self):
        """
        概要: Flaskアプリケーションの実行
        """
        self.flask_app.run(host=FLASK_HOST, port=FLASK_PORT)

class MainWindow(QMainWindow):
    """
    概要: メインウィンドウクラス
    用途: PySide6のメインウィンドウとWebEngineViewの管理
    """
    
    def __init__(self):
        """
        概要: ウィンドウの初期化とWebEngineViewの設定
        """
        super().__init__()
        self.setWindowTitle(WINDOW_TITLE)
        self.setGeometry(100, 100, WINDOW_WIDTH, WINDOW_HEIGHT)
        
        self.web_view = QWebEngineView()
        self.web_view.setUrl(QUrl(VITE_URL))
        self.setCentralWidget(self.web_view)

def cleanup(react_server):
    """
    概要: アプリケーション終了時のクリーンアップ処理
    """
    print("アプリケーションを終了します...")
    react_server.stop()
    sys.exit(0)

try:
    # React開発サーバーを起動
    react_server = ReactDevServer()
    react_server.start()
    print("React開発サーバーを起動しました")
    
    # シグナルハンドラの設定
    signal.signal(signal.SIGINT, lambda s, f: cleanup(react_server))
    signal.signal(signal.SIGTERM, lambda s, f: cleanup(react_server))
    
    # Flaskアプリケーションをバックグラウンドで起動
    flask_thread = FlaskAppThread()
    flask_thread.daemon = True
    flask_thread.start()
    print("Flaskサーバーを起動しました")
    
    # PySide6アプリケーションの初期化と実行
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    print("アプリケーションウィンドウを表示しました")
    
    # アプリケーション終了時のクリーンアップを設定
    app.aboutToQuit.connect(lambda: cleanup(react_server))
    
    sys.exit(app.exec())

except Exception as e:
    if 'react_server' in locals():
        react_server.stop()
    trace = get_exception_trace()
    print("エラーが発生しました:", "".join(trace))
    sys.exit(1)