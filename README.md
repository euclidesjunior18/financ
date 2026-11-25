# 💰 FinanPy - Administrador Financeiro Inteligente

Sistema web completo de controle e planejamento financeiro desenvolvido em **Python (Flask)** com banco de dados **SQLite**, no formato de **planilha financeira ativa**.

Ele foi projetado para resolver o problema clássico de planilhas manuais: **repassar automaticamente receitas e despesas recorrentes** (como aluguel, salário, assinaturas) e gerenciar despesas com **prazo limite** (como compras parceladas em 3x, 10x, 24x), controlando a evolução do saldo mês a mês.

---

## 📌 Funcionalidades Principais

- 🔄 **Recorrência Automática para os Meses**:
  - **Para Sempre (Recorrente Fixo)**: Cadastre despesas fixas (aluguel, condomínio, internet) ou receitas (salário, rendimentos). O sistema projeta automaticamente em todos os meses futuros.
  - **Parcelado (com Prazo Limite)**: Cadastre parcelas (ex: *10 parcelas mensais*). O sistema calcula dinamicamente o status (ex: *Parcela 1/10*, *Parcela 2/10*) e encerra o repasse automaticamente ao término.
  - **Lançamento Único**: Gastos pontuais restritos ao mês de lançamento.
- ✏️ **Edição Flexível de Despesas e Receitas**:
  - **Permanente**: Altera valor, descrição e categoria na regra geral (afeta todos os meses).
  - **Pontual / Apenas no Mês**: Ajusta o valor somente no mês selecionado (ideal para oscilações como conta de luz/água).
- 📅 **Visão Mensal Interativa**:
  - Totalizadores automáticos: Total de Receitas, Total de Despesas, Saldo Previsto e Saldo Realizado.
  - Checkbox dinâmico para marcar recebimentos e pagamentos efetuados.
- 📊 **Planilha Anual Projetada**:
  - Visão panorâmica dos 12 meses do ano com saldo acumulado e projeções de fluxo de caixa.
- ⚙️ **Gerenciador de Recorrências**:
  - Painel exclusivo para auditar e gerenciar contratos, prazos e regras ativas.

---

## 🏗️ Arquitetura e Tecnologias

- **Linguagem**: Python 3.10+
- **Framework Web**: Flask
- **Banco de Dados**: SQLite (nativo, leve e sem necessidade de servidor externo)
- **Front-end**: HTML5, CSS3, Bootstrap 5, Bootstrap Icons (responsivo para Desktop e Mobile)
- **Servidor WSGI para Produção**: Gunicorn

### Estrutura de Arquivos

```text
├── app.py               # Rotas HTTP, controladores e inicialização da aplicação
├── database.py          # Conexão SQLite, schemas e manipulação de datas
├── finance_manager.py   # Motor de projeção mensal/anual e regras de parcelas
├── templates/           # Telas da interface (HTML + Jinja2)
│   ├── base.html        # Layout padrão e componentes globais
│   ├── index.html       # Planilha de visualização mensal e formulários
│   ├── anual.html       # Projeção anual consolidada
│   └── cadastros.html   # Gerenciador de regras e parcelas
├── Dockerfile           # Imagem conteinerizada para produção
├── docker-compose.yml   # Orquestração local simplificada com Docker
├── requirements.txt     # Dependências Python
└── Procfile             # Configuração para deploy (Heroku, Render, Railway)
```

---

## 💻 Como Executar Localmente

### Pré-requisitos
- Python 3.10 ou superior instalado.
- Gerenciador de pacotes `pip`.

### Passo a Passo

1. **Clone o repositório:**
   ```bash
   git clone https://github.com/euclidesjunior18/financ.git
   cd financ
   ```

2. **(Opcional) Crie e ative um ambiente virtual:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # Linux/macOS
   # No Windows: venv\Scripts\activate
   ```

3. **Instale as dependências:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Inicie o servidor de desenvolvimento:**
   ```bash
   python3 app.py
   ```

5. **Acesse no navegador:**
   Abra [http://localhost:5000](http://localhost:5000)

---

## 🐳 Executando com Docker

Se preferir rodar isolado em container:

```bash
# Construir e rodar via Docker Compose
docker compose up -d

# Ou construir e rodar diretamente:
docker build -t financ-app .
docker run -p 5000:5000 financ-app
```

Acesse em [http://localhost:5000](http://localhost:5000).

---

## 🚀 Como Fazer Deploy

A aplicação já inclui `Procfile` e `Dockerfile`, tornando o deploy imediato em diversas plataformas:

### 1. Render (Recomendado - Gratuito)
1. Crie uma conta no [Render](https://render.com/).
2. Clique em **New** > **Web Service**.
3. Conecte seu repositório GitHub `financ`.
4. Defina:
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`
5. Clique em **Create Web Service**.

### 2. Railway
1. Acesse o [Railway](https://railway.app/).
2. Clique em **New Project** > **Deploy from GitHub repo**.
3. Selecione o repositório `financ`.
4. O Railway detectará o `Procfile` ou `Dockerfile` automaticamente e iniciará a aplicação.

### 3. VPS / Servidor Próprio (Ubuntu/Debian)
1. Instale o Nginx e Python:
   ```bash
   sudo apt update && sudo apt install python3-pip python3-venv nginx -y
   ```
2. Clone o repositório e crie um serviço systemd para rodar o Gunicorn:
   ```bash
   gunicorn --workers 3 --bind 127.0.0.1:5000 app:app
   ```
3. Configure o Nginx como proxy reverso para `127.0.0.1:5000`.

---

## 📄 Licença

Este projeto é de código aberto sob a licença [MIT](https://opensource.org/licenses/MIT).
