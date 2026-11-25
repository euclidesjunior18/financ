"""
Sistema de Gerenciamento Financeiro - Modelos e Banco de Dados (SQLite)
"""
import sqlite3
import os
from datetime import datetime

DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "finance.db")

def get_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    # Tabela de Itens Financeiros (Receitas e Despesas Recorrentes ou Fixas)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS financial_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        description TEXT NOT NULL,
        amount REAL NOT NULL,
        type TEXT NOT NULL CHECK(type IN ('receita', 'despesa')),
        category TEXT DEFAULT 'Geral',
        start_month TEXT NOT NULL, -- formato YYYY-MM
        duration_type TEXT NOT NULL CHECK(duration_type IN ('indefinido', 'parcelado', 'unico')),
        installments_count INTEGER DEFAULT NULL, -- quantidade de parcelas se for parcelado
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Tabela de Ajustes / Sobrescrita por mês específico (ex: marcar como pago, alterar valor pontual ou excluir só num mês)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS month_overrides (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        item_id INTEGER NOT NULL,
        month_str TEXT NOT NULL, -- formato YYYY-MM
        is_paid INTEGER DEFAULT 0, -- 1 se pago, 0 se pendente
        override_amount REAL DEFAULT NULL, -- se alterou o valor especificamente neste mês
        is_deleted INTEGER DEFAULT 0, -- 1 se foi desativado/ignorado especificamente neste mês
        notes TEXT DEFAULT '',
        FOREIGN KEY (item_id) REFERENCES financial_items (id) ON DELETE CASCADE,
        UNIQUE(item_id, month_str)
    )
    """)

    # Tabela para Lançamentos Avulsos (gastos pontuais do dia a dia não recorrentes)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS one_time_transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        description TEXT NOT NULL,
        amount REAL NOT NULL,
        type TEXT NOT NULL CHECK(type IN ('receita', 'despesa')),
        category TEXT DEFAULT 'Geral',
        date_str TEXT NOT NULL, -- YYYY-MM-DD
        month_str TEXT NOT NULL, -- YYYY-MM
        is_paid INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    conn.close()

def add_months(year_month_str, months_to_add):
    """Calcula YYYY-MM somando/subtraindo meses"""
    year, month = map(int, year_month_str.split("-"))
    total_months = year * 12 + (month - 1) + months_to_add
    new_year = total_months // 12
    new_month = (total_months % 12) + 1
    return f"{new_year:04d}-{new_month:02d}"

def month_difference(start_ym, current_ym):
    """Retorna a diferença em meses entre start_ym e current_ym (current - start)"""
    y1, m1 = map(int, start_ym.split("-"))
    y2, m2 = map(int, current_ym.split("-"))
    return (y2 - y1) * 12 + (m2 - m1)
