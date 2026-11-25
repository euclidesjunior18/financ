import os
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, jsonify, flash
from database import init_db, get_connection, add_months
import finance_manager

app = Flask(__name__)
app.secret_key = "financ-super-secret-key-2026"

# Inicializar o banco de dados
init_db()

@app.template_filter('currency')
def currency_filter(value):
    try:
        val = float(value)
        return f"R$ {val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except (ValueError, TypeError):
        return f"R$ 0,00"

@app.template_filter('month_name')
def month_name_filter(month_str):
    try:
        y, m = month_str.split("-")
        meses = {
            "01": "Janeiro", "02": "Fevereiro", "03": "Março",
            "04": "Abril", "05": "Maio", "06": "Junho",
            "07": "Julho", "08": "Agosto", "09": "Setembro",
            "10": "Outubro", "11": "Novembro", "12": "Dezembro"
        }
        return f"{meses.get(m, m)} de {y}"
    except Exception:
        return month_str

@app.route("/")
def index():
    # Mês padrão atual ou passado por parâmetro
    current_month = request.args.get("month")
    if not current_month:
        now = datetime.now()
        current_month = f"{now.year:04d}-{now.month:02d}"

    data = finance_manager.get_month_data(current_month)
    return render_template("index.html", data=data, current_month=current_month)

@app.route("/anual")
def anual():
    year = request.args.get("year", str(datetime.now().year))
    summary = finance_manager.get_yearly_summary(year)
    total_anual_receita = sum(m['receitas'] for m in summary)
    total_anual_despesa = sum(m['despesas'] for m in summary)
    total_anual_saldo = total_anual_receita - total_anual_despesa
    
    return render_template(
        "anual.html",
        year=year,
        summary=summary,
        total_anual_receita=total_anual_receita,
        total_anual_despesa=total_anual_despesa,
        total_anual_saldo=total_anual_saldo,
        prev_year=str(int(year) - 1),
        next_year=str(int(year) + 1)
    )

@app.route("/cadastros")
def cadastros():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM financial_items ORDER BY id DESC")
    items = cursor.fetchall()
    conn.close()
    return render_template("cadastros.html", items=items)

@app.route("/item/add", methods=["POST"])
def add_item():
    description = request.form.get("description", "").strip()
    amount_str = request.form.get("amount", "0").replace(".", "").replace(",", ".")
    try:
        amount = float(amount_str)
    except ValueError:
        amount = 0.0

    item_type = request.form.get("type", "despesa")
    category = request.form.get("category", "Geral").strip() or "Geral"
    start_month = request.form.get("start_month", datetime.now().strftime("%Y-%m"))
    duration_type = request.form.get("duration_type", "indefinido")
    installments_count = request.form.get("installments_count")

    if duration_type == "parcelado" and installments_count:
        installments_count = int(installments_count)
    else:
        installments_count = None

    if description and amount > 0:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO financial_items (description, amount, type, category, start_month, duration_type, installments_count)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (description, amount, item_type, category, start_month, duration_type, installments_count))
        conn.commit()
        conn.close()
        flash("Item cadastrado com sucesso!", "success")
    else:
        flash("Preencha descrição e um valor válido maior que zero.", "warning")

    redirect_month = request.form.get("redirect_month", start_month)
    return redirect(url_for("index", month=redirect_month))

@app.route("/item/edit", methods=["POST"])
def edit_item():
    item_id = request.form.get("item_id")
    month_str = request.form.get("month_str")
    scope = request.form.get("scope", "permanent") # "permanent" (todos os meses) ou "month_only" (apenas este mês)
    description = request.form.get("description", "").strip()
    amount_str = request.form.get("amount", "0").replace(".", "").replace(",", ".")
    category = request.form.get("category", "Geral").strip() or "Geral"
    item_type = request.form.get("type", "despesa")
    duration_type = request.form.get("duration_type")
    installments_count = request.form.get("installments_count")

    try:
        amount = float(amount_str)
    except ValueError:
        amount = 0.0

    if not description or amount <= 0:
        flash("Preencha descrição e um valor válido maior que zero.", "warning")
        return redirect(request.referrer or url_for("index", month=month_str))

    conn = get_connection()
    cursor = conn.cursor()

    if scope == "month_only" and month_str:
        # Altera apenas o valor para este mês específico
        cursor.execute("SELECT id FROM month_overrides WHERE item_id = ? AND month_str = ?", (item_id, month_str))
        row = cursor.fetchone()
        if row:
            cursor.execute("UPDATE month_overrides SET override_amount = ? WHERE item_id = ? AND month_str = ?", (amount, item_id, month_str))
        else:
            cursor.execute("""
                INSERT INTO month_overrides (item_id, month_str, override_amount)
                VALUES (?, ?, ?)
            """, (item_id, month_str, amount))
        flash(f"Valor alterado exclusivamente para o mês {month_str}!", "success")
    else:
        # Atualiza o cadastro base (permanente em todos os meses)
        if duration_type == "parcelado" and installments_count:
            inst_count = int(installments_count)
        else:
            inst_count = None

        if duration_type:
            cursor.execute("""
                UPDATE financial_items
                SET description = ?, amount = ?, category = ?, type = ?, duration_type = ?, installments_count = ?
                WHERE id = ?
            """, (description, amount, category, item_type, duration_type, inst_count, item_id))
        else:
            cursor.execute("""
                UPDATE financial_items
                SET description = ?, amount = ?, category = ?, type = ?
                WHERE id = ?
            """, (description, amount, category, item_type, item_id))

        flash("Item atualizado com sucesso para todos os meses!", "success")

    conn.commit()
    conn.close()

    redirect_month = request.form.get("redirect_month", month_str)
    if redirect_month:
        return redirect(url_for("index", month=redirect_month))
    return redirect(request.referrer or url_for("cadastros"))

@app.route("/item/toggle_paid", methods=["POST"])
def toggle_paid():
    item_id = request.form.get("item_id")
    month_str = request.form.get("month_str")
    is_avulso = request.form.get("is_avulso") == "true"

    conn = get_connection()
    cursor = conn.cursor()

    if is_avulso:
        cursor.execute("SELECT is_paid FROM one_time_transactions WHERE id = ?", (item_id,))
        row = cursor.fetchone()
        if row:
            new_val = 0 if row["is_paid"] == 1 else 1
            cursor.execute("UPDATE one_time_transactions SET is_paid = ? WHERE id = ?", (new_val, item_id))
    else:
        cursor.execute("SELECT is_paid FROM month_overrides WHERE item_id = ? AND month_str = ?", (item_id, month_str))
        row = cursor.fetchone()
        if row:
            new_val = 0 if row["is_paid"] == 1 else 1
            cursor.execute("UPDATE month_overrides SET is_paid = ? WHERE item_id = ? AND month_str = ?", (new_val, item_id, month_str))
        else:
            # Novo override marcando como pago (1)
            cursor.execute("""
                INSERT INTO month_overrides (item_id, month_str, is_paid)
                VALUES (?, ?, 1)
            """, (item_id, month_str))

    conn.commit()
    conn.close()
    return redirect(url_for("index", month=month_str))

@app.route("/item/delete_month_instance", methods=["POST"])
def delete_month_instance():
    """Remove a recorrência especificamente para o mês selecionado"""
    item_id = request.form.get("item_id")
    month_str = request.form.get("month_str")
    is_avulso = request.form.get("is_avulso") == "true"

    conn = get_connection()
    cursor = conn.cursor()

    if is_avulso:
        cursor.execute("DELETE FROM one_time_transactions WHERE id = ?", (item_id,))
    else:
        cursor.execute("SELECT id FROM month_overrides WHERE item_id = ? AND month_str = ?", (item_id, month_str))
        row = cursor.fetchone()
        if row:
            cursor.execute("UPDATE month_overrides SET is_deleted = 1 WHERE item_id = ? AND month_str = ?", (item_id, month_str))
        else:
            cursor.execute("""
                INSERT INTO month_overrides (item_id, month_str, is_deleted)
                VALUES (?, ?, 1)
            """, (item_id, month_str))

    conn.commit()
    conn.close()
    flash("Item removido deste mês.", "info")
    return redirect(url_for("index", month=month_str))

@app.route("/item/delete_permanent/<int:item_id>", methods=["POST"])
def delete_permanent(item_id):
    """Exclui a regra recorrente por completo de todos os meses"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM month_overrides WHERE item_id = ?", (item_id,))
    cursor.execute("DELETE FROM financial_items WHERE id = ?", (item_id,))
    conn.commit()
    conn.close()
    flash("Item removido permanentemente de todos os meses.", "info")
    return redirect(request.referrer or url_for("cadastros"))

@app.route("/item/avulso/add", methods=["POST"])
def add_avulso():
    description = request.form.get("description", "").strip()
    amount_str = request.form.get("amount", "0").replace(".", "").replace(",", ".")
    try:
        amount = float(amount_str)
    except ValueError:
        amount = 0.0

    item_type = request.form.get("type", "despesa")
    category = request.form.get("category", "Geral").strip() or "Geral"
    date_str = request.form.get("date_str", datetime.now().strftime("%Y-%m-%d"))
    month_str = date_str[:7] # YYYY-MM

    if description and amount > 0:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO one_time_transactions (description, amount, type, category, date_str, month_str, is_paid)
            VALUES (?, ?, ?, ?, ?, ?, 1)
        """, (description, amount, item_type, category, date_str, month_str))
        conn.commit()
        conn.close()
        flash("Lançamento avulso registrado com sucesso!", "success")

    return redirect(url_for("index", month=month_str))

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
