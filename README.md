# Sistema de Gerenciamento de Chamados (Flask + MySQL)

Aplicação Flask para gerenciar chamados e interações de uma firma terceirizada, com autenticação de usuários, CRUD de chamados e interações, e exportação para CSV.

## Recursos
- Cadastro/Login/Logout (Flask-Login)
- Perfis: Admin e Usuário comum
- CRUD de Chamados (título, descrição, status, prioridade, responsável, terceirizada)
- CRUD de Interações atreladas ao chamado
- Exportação CSV de chamados e interações
- Migrações de banco (Flask-Migrate)

## Requisitos
- Python 3.10+
- MySQL 8+ em execução local

## Configuração
1. Copie `.env.example` para `.env` e ajuste `SECRET_KEY` e `DATABASE_URL`.

   Exemplo de `DATABASE_URL`:
   ```
   mysql+pymysql://root:senha@localhost:3306/chamados_db
   ```

   Opcional (SQLite para testes rápidos):
   ```powershell
   Copy-Item .env.sqlite.example .env -Force
   ```
   Isso usará `sqlite:///dev.db` no diretório do projeto.

2. Crie e ative um ambiente virtual e instale dependências (PowerShell):
   ```powershell
   py -3 -m venv .venv; .\.venv\Scripts\Activate.ps1; pip install -r requirements.txt
   ```

3. Inicialize o banco e migrações:
   ```powershell
   $env:FLASK_APP="wsgi.py"; $env:FLASK_ENV="development"; flask db init; flask db migrate -m "init"; flask db upgrade
   ```

4. Crie um usuário admin (shell Flask):
   ```powershell
   flask shell
   >>> from app.extensions import db
   >>> from app.models import User
   >>> u=User(name="Admin", email="admin@empresa.com", role="admin"); u.set_password("admin123"); db.session.add(u); db.session.commit()
   >>> exit()
   ```

5. Rodar o servidor:
   ```powershell
   flask run
   ```

Acesse http://127.0.0.1:8443

## Estrutura
- `app/__init__.py`: criação do app, blueprints
- `app/extensions.py`: db, login_manager, migrate
- `app/models.py`: User, Ticket, Interaction
- `app/forms.py`: WTForms
- `app/routes.py`: rotas principais
- `app/templates/`: HTML (Bootstrap 5)
- `wsgi.py`: ponto de entrada

## Exportação CSV
- Botões nas páginas listam e exportam dados filtrados.

## Licença
Uso interno. Ajuste conforme sua necessidade.
