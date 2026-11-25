"""
Lógica para cálculo de dados mensais, projeção de recorrências e parcelas.
"""
from database import get_connection, month_difference, add_months

def get_month_data(month_str):
    """
    Retorna todo o balanço de um determinado mês (YYYY-MM), incluindo:
    - Itens recorrentes válidos para esse mês (com indicação de parcela se aplicável)
    - Gastos pontuais do mês
    - Totais de receitas, despesas e saldo
    """
    conn = get_connection()
    cursor = conn.cursor()

    # Buscar itens base recorrentes
    cursor.execute("""
        SELECT * FROM financial_items
        ORDER BY id ASC
    """)
    items = cursor.fetchall()

    # Buscar overrides deste mês
    cursor.execute("""
        SELECT * FROM month_overrides WHERE month_str = ?
    """, (month_str,))
    overrides = {row['item_id']: dict(row) for row in cursor.fetchall()}

    # Buscar transações avulsas
    cursor.execute("""
        SELECT * FROM one_time_transactions WHERE month_str = ?
        ORDER BY date_str DESC, id DESC
    """, (month_str,))
    avulsas = [dict(row) for row in cursor.fetchall()]

    active_items = []
    total_receitas = 0.0
    total_despesas = 0.0
    total_receitas_pagas = 0.0
    total_despesas_pagas = 0.0

    for item_row in items:
        item = dict(item_row)
        start_month = item['start_month']
        diff = month_difference(start_month, month_str)

        # Se o mês pesquisado for anterior ao início, não aparece
        if diff < 0:
            continue

        item_id = item['id']
        override = overrides.get(item_id, {})

        # Se foi deletado ou ignorado neste mês específico
        if override.get('is_deleted', 0) == 1:
            continue

        is_active = False
        parcela_label = ""

        if item['duration_type'] == 'indefinido':
            # Para sempre a partir do start_month
            is_active = True
            parcela_label = "Recorrente fixo"
        elif item['duration_type'] == 'parcelado':
            installments = item['installments_count'] or 1
            if 0 <= diff < installments:
                is_active = True
                parcela_label = f"Parcela {diff + 1}/{installments}"
        elif item['duration_type'] == 'unico':
            if diff == 0:
                is_active = True
                parcela_label = "Mês único"

        if is_active:
            amount = override.get('override_amount') if override.get('override_amount') is not None else item['amount']
            is_paid = bool(override.get('is_paid', 0))

            computed_item = {
                'id': item_id,
                'description': item['description'],
                'amount': amount,
                'original_amount': item['amount'],
                'type': item['type'],
                'category': item['category'],
                'start_month': item['start_month'],
                'duration_type': item['duration_type'],
                'parcela_label': parcela_label,
                'is_paid': is_paid,
                'is_override': override.get('override_amount') is not None,
                'is_avulso': False
            }
            active_items.append(computed_item)

            if item['type'] == 'receita':
                total_receitas += amount
                if is_paid:
                    total_receitas_pagas += amount
            else:
                total_despesas += amount
                if is_paid:
                    total_despesas_pagas += amount

    # Somar avulsos
    for av in avulsas:
        amount = av['amount']
        is_paid = bool(av.get('is_paid', 1))
        item_data = {
            'id': av['id'],
            'description': av['description'],
            'amount': amount,
            'type': av['type'],
            'category': av['category'],
            'start_month': av['month_str'],
            'duration_type': 'avulso',
            'parcela_label': 'Lançamento Avulso',
            'is_paid': is_paid,
            'is_avulso': True,
            'date_str': av['date_str']
        }
        active_items.append(item_data)
        if av['type'] == 'receita':
            total_receitas += amount
            if is_paid:
                total_receitas_pagas += amount
        else:
            total_despesas += amount
            if is_paid:
                total_despesas_pagas += amount

    saldo = total_receitas - total_despesas
    saldo_realizado = total_receitas_pagas - total_despesas_pagas

    conn.close()

    # Ordenar: Receitas primeiro, depois Despesas
    receitas_list = [i for i in active_items if i['type'] == 'receita']
    despesas_list = [i for i in active_items if i['type'] == 'despesa']

    return {
        'month_str': month_str,
        'receitas': receitas_list,
        'despesas': despesas_list,
        'total_receitas': total_receitas,
        'total_despesas': total_despesas,
        'total_receitas_pagas': total_receitas_pagas,
        'total_despesas_pagas': total_despesas_pagas,
        'saldo': saldo,
        'saldo_realizado': saldo_realizado,
        'prev_month': add_months(month_str, -1),
        'next_month': add_months(month_str, 1)
    }

def get_yearly_summary(year_str):
    """Gera projeção para os 12 meses do ano selecionado (estilo planilha anual)"""
    months_data = []
    for m in range(1, 13):
        m_str = f"{year_str}-{m:02d}"
        data = get_month_data(m_str)
        months_data.append({
            'month': m_str,
            'receitas': data['total_receitas'],
            'despesas': data['total_despesas'],
            'saldo': data['saldo']
        })
    return months_data
