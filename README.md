# Espaço Delas — Sistema de Agendamento Online

> Sistema web de agendamento para studio de beleza feminino, desenvolvido com Django + TailwindCSS como projeto de TCC.

---

## 📋 Pré-requisitos

Antes de começar, certifique-se de ter instalado:

- [Python 3.12+](https://www.python.org/downloads/)
- [Git](https://git-scm.com/)
- (Opcional para produção) [PostgreSQL 16+](https://www.postgresql.org/) e [Redis 7+](https://redis.io/)

---

## 🚀 Instalação e Configuração

### 1. Clone o repositório

```bash
git clone https://github.com/seu-usuario/espaco-delas.git
cd espaco-delas
```

### 2. Crie e ative o ambiente virtual

```bash
# Criar o ambiente virtual
python -m venv .venv

# Ativar no Windows (PowerShell)
.venv\Scripts\Activate.ps1

# Ativar no Windows (CMD)
.venv\Scripts\activate.bat

# Ativar no Linux/macOS
source .venv/bin/activate
```

### 3. Instale as dependências

```bash
pip install -r requirements.txt
```

### 4. Configure as variáveis de ambiente

Copie o arquivo de exemplo e ajuste os valores conforme o seu ambiente:

```bash
# Windows (PowerShell)
Copy-Item .env.example .env

# Linux/macOS
cp .env.example .env
```

Edite o arquivo `.env` gerado com suas configurações:

```env
# Django
SECRET_KEY=sua-chave-secreta-aqui   # Gere uma chave segura (veja abaixo)
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost

# Banco de dados (deixe comentado para usar SQLite no desenvolvimento)
# DATABASE_URL=postgres://usuario:senha@localhost:5432/espaco_delas

# E-mail (console para desenvolvimento — os e-mails aparecem no terminal)
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
```

> **Dica:** Para gerar uma `SECRET_KEY` segura, execute:
> ```bash
> python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
> ```

### 5. Execute as migrações do banco de dados

```bash
python manage.py migrate
```

### 6. Popule o banco com dados iniciais

O script cria as profissionais, serviços e grades de horários padrão, além do superusuário administrador:

```bash
python populate_db.py
```

Após executar, os seguintes usuários estarão disponíveis:

| Usuário       | Senha      | Função               |
|---------------|------------|----------------------|
| `admin`       | `admin123` | Superusuário / Owner |
| `alessandra`  | `senha123` | Manicure             |
| `luana`       | `senha123` | Manicure             |
| `larissa`     | `senha123` | Designer de Sobrancelhas |

> ⚠️ **Importante:** Altere essas senhas antes de publicar o projeto em produção.

### 7. Compile os arquivos CSS com TailwindCSS

O projeto utiliza o binário standalone do TailwindCSS. Execute o comando de build (ou watch para desenvolvimento):

```bash
# Modo watch (recompila automaticamente ao editar templates)
.\tailwindcss.exe -i ./static/css/input.css -o ./static/css/output.css --watch

# Ou apenas um build único
.\tailwindcss.exe -i ./static/css/input.css -o ./static/css/output.css --minify
```

### 8. Colete os arquivos estáticos (opcional em dev)

```bash
python manage.py collectstatic
```

---

## ▶️ Rodando o servidor de desenvolvimento

```bash
python manage.py runserver
```

Acesse no navegador: [http://127.0.0.1:8000](http://127.0.0.1:8000)

Painel administrativo Django: [http://127.0.0.1:8000/admin](http://127.0.0.1:8000/admin)

---

## 🗂️ Estrutura do Projeto

```
espaco-delas/
├── accounts/        # App de autenticação e perfis de profissionais
├── booking/         # App de agendamento (serviços, horários, appointments)
├── config/          # Configurações do Django (settings, urls, wsgi)
├── core/            # App da página institucional (home)
├── dashboard/       # App do painel administrativo das profissionais
├── media/           # Uploads de imagens (fotos de profissionais, galeria)
├── static/          # Arquivos estáticos (CSS, JS, imagens)
├── templates/       # Templates HTML (Django Template Language)
├── .env.example     # Exemplo de variáveis de ambiente
├── manage.py        # Utilitário de linha de comando do Django
├── populate_db.py   # Script para popular o banco com dados iniciais
├── requirements.txt # Dependências Python
└── tailwind.config.js # Configuração do TailwindCSS
```

---

## 📦 Dependências principais

| Pacote               | Versão   | Uso                              |
|----------------------|----------|----------------------------------|
| Django               | ≥ 5.1    | Framework web                    |
| python-decouple      | ≥ 3.8    | Gerenciamento de variáveis de ambiente |
| Pillow               | ≥ 10.0   | Processamento de imagens         |
| psycopg2-binary      | ≥ 2.9    | Conector PostgreSQL (produção)   |
| gunicorn             | ≥ 22.0   | Servidor WSGI (produção)         |
| celery               | ≥ 5.4    | Tarefas assíncronas (e-mails agendados) |
| redis                | ≥ 5.0    | Broker para o Celery             |
| django-celery-beat   | ≥ 2.6    | Agendamento periódico de tarefas |

---

## 📧 Configuração de E-mail (Produção)

Para envio real de e-mails, configure no `.env`:

```env
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.sendgrid.net
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=apikey
EMAIL_HOST_PASSWORD=sua-api-key-sendgrid
```

---

## ⚙️ Tarefas Assíncronas com Celery (Opcional)

Para habilitar lembretes automáticos por e-mail (24h antes do agendamento), inicie o Celery com Redis:

```bash
# Certifique-se de que o Redis está rodando localmente
# Em outro terminal, inicie o worker do Celery
celery -A config worker --loglevel=info

# Em outro terminal, inicie o beat (agendador de tarefas periódicas)
celery -A config beat --loglevel=info
```

Configure no `.env`:

```env
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

---

## 🧪 Executando os Testes

```bash
python manage.py test
```

---

## 📄 Documentação do Produto

Consulte o [PRD completo](./PRD_espaco_delas.md) para detalhes sobre requisitos funcionais, design system, fluxos de UX e critérios de aceite.

---

## 📝 Licença

Projeto acadêmico — Trabalho de Conclusão de Curso (TCC). Todos os direitos reservados.
