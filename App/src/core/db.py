import sqlite3
import os

DB_PATH = "interactables.sqlite3"

def _get_connection():
    # Cria o banco na raiz do projeto (ou no diretório atual de execução)
    return sqlite3.connect(DB_PATH)

def init_db():
    """
    Cria a estrutura inicial do banco de dados local para configurações e histórico.
    """
    conn = _get_connection()
    cursor = conn.cursor()
    
    # Tabela de preferências (ex: dark mode, resolução padrão)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    ''')
    
    # Tabela de histórico de projetos abertos recentemente
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS recent_projects (
            path TEXT PRIMARY KEY,
            last_opened TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

def save_setting(key: str, value: str):
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO settings (key, value)
        VALUES (?, ?)
    ''', (key, value))
    conn.commit()
    conn.close()

def get_setting(key: str, default: str = None) -> str:
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT value FROM settings WHERE key = ?', (key,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else default

def add_recent_project(path: str):
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO recent_projects (path, last_opened)
        VALUES (?, CURRENT_TIMESTAMP)
    ''', (path,))
    conn.commit()
    conn.close()

