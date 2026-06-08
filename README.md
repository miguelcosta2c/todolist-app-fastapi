# 📝 TodoList App

[![Python Version](https://img.shields.io/badge/python-3.13-blue.svg)](https://www.python.org/)
[![FastAPI Version](https://img.shields.io/badge/FastAPI-0.136%2B-009688.svg)](https://fastapi.tiangolo.com/)
[![React Version](https://img.shields.io/badge/React-19-61DAFB.svg)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-6.0-3178C6.svg)](https://www.typescriptlang.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-17-4169E1.svg)](https://www.postgresql.org/)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED.svg)](https://www.docker.com/)
[![Coverage](https://img.shields.io/badge/Coverage-100%25-brightgreen.svg)](#)

Uma aplicação _full-stack_ robusta para gerenciamento de tarefas, equipada com autenticação JWT segura (mecanismo de rotação de tokens), painel administrativo completo, filtros avançados de busca, paginação e suporte a exclusão lógica (_soft-delete_).

---

## 🚀 Principais Funcionalidades

### 👤 Usuário Comum

- **Autenticação Segura:** Cadastro com validação estrita de senha e login baseado em JWT.
- **Gerenciamento de Tarefas:** CRUD completo de tarefas com estados descritivos (`TODO` ↔ `IN_PROGRESS` ↔ `DONE`).
- **Busca & Filtros Avançados:** Filtros por status, prioridade, intervalo de datas e busca textual otimizada com _debounce_ de 300ms.
- **Ordenação e Paginação:** Listagem flexível controlada por paginação baseada em _offset_.
- **UX Fluida:** Interface responsiva com suporte a _Dark Mode_ automático (detectado via sistema) ou manual, além de notificações em tempo real (_toasts_).
- **Privacidade:** Opção de encerramento de conta via _soft-delete_.

### 👑 Painel Administrativo (`is_superuser`)

- **Dashboard Exclusivo:** Sidebar administrativa visível apenas para contas autorizadas.
- **Controle de Usuários:** CRUD de qualquer usuário cadastrado no sistema.
- **Auditoria de Tarefas:** Visualização e manipulação de qualquer tarefa do ecossistema, incluindo identificação do proprietário.
- **Segurança de Sessões:** Listagem, revogação forçada e exclusão de _refresh tokens_ ativos de qualquer conta.
- **Filtros de Auditoria:** Busca avançada incluindo registros marcados como excluídos (_include_deleted_).

### 🔒 Mecanismos de Segurança

- **Criptografia:** Senhas criptografadas utilizando o algoritmo **Argon2 ID**.
- **Estratégia JWT:** _Access token_ de vida curta (30 minutos) transmitido em memória/payload e _Refresh token_ de vida longa (7 dias) armazenado em cookie seguro (`httpOnly`, `Secure` e `SameSite=Lax`) com rotação automática.
- **Axios Interceptors:** Atualização transparente de tokens no _frontend_ com fila de requisições concorrentes para evitar gargalos após a expiração.
- **Proteção de Infraestrutura:** _Rate limiting_ por rotas via `slowapi`, proteção de cabeçalhos com `TrustedHostMiddleware` e políticas estritas de CORS.

---

## 🛠️ Tech Stack

### Frontend

- **Linguagem & Core:** TypeScript (~6.0), React (v19)
- **Build Tool:** Vite (v8)
- **Roteamento:** react-router-dom (v7)
- **Gerenciamento de Estado de Servidor:** TanStack React Query (v5)
- **Formulários & Validação:** react-hook-form (v7) + Zod (v3)
- **Estilização & Componentes:** Tailwind CSS (v3.4) + shadcn/ui (Radix Primitives)
- **Utilidades:** Axios (v1.9), Sonner (Toasts), Lucide React (Ícones)

### Backend

- **Linguagem & Framework:** Python (v3.13) + FastAPI (v0.136+)
- **Servidor ASGI:** Uvicorn (v0.48+)
- **Banco de Dados & ORM:** PostgreSQL (v17) + SQLAlchemy (v2.0+) utilizando conexões assíncronas (`asyncpg`)
- **Migrações de Banco:** Alembic (v1.18+)
- **Camada de Validação:** Pydantic (v2.13+)
- **Segurança:** Argon2 (via passlib), python-jose, slowapi (Rate limit)
- **Testes:** pytest + testcontainers (Ambiente isolado PostgreSQL)

---

## 📁 Estrutura do Projeto

```text
todolist-app/
├── .github/workflows/ci.yml     # Pipeline de Integração Contínua (CI)
├── backend/
│   ├── src/app/
│   │   ├── api/                  # Endpoints/Routers (auth, user, todo, admin)
│   │   ├── core/                 # Dependências, segurança, configurações e limites
│   │   ├── models/               # Modelos SQLAlchemy (User, Todo, UserToken)
│   │   ├── services/             # Regras de negócio e consultas ao banco (queries)
│   │   ├── schemas.py            # Schemas de entrada/saída do Pydantic
│   │   ├── main.py               # Instanciação da factory do FastAPI
│   │   ├── db.py                 # Inicialização da Engine e Sessão Assíncrona
│   │   ├── exc.py                # Definição de exceções customizadas
│   │   └── exc_handlers.py       # Interceptadores globais de erros/exceções
│   ├── alembic/                  # Arquivos de migração do banco de dados
│   ├── tests/                    # Suíte com 161 testes automatizados (100% de cobertura)
│   └── Dockerfile                # Build multi-stage (builder, dev, prod)
├── frontend/
│   ├── src/
│   │   ├── api/                  # Clientes HTTP e chamadas de API (auth, todos, admin)
│   │   ├── components/           # Componentes de interface (shadcn) e estruturais
│   │   ├── hooks/                # Custom hooks (useAuth, useTodos, useAdmin, etc.)
│   │   ├── pages/                # Páginas e telas da aplicação SPA
│   │   ├── providers/            # Provedores de Contexto (Auth, Query, Theme)
│   │   └── types/                # Definições de tipos TypeScript
│   └── Dockerfile                # Build multi-stage otimizado com Nginx para prod
├── docker-compose.yaml           # Orquestração local (frontend, api, db)
└── justfile                      # Orquestrador de tarefas/atalhos de desenvolvimento
```

---

## ⚙️ Configuração do Ambiente Local

### Pré-requisitos

- [Docker & Docker Compose](https://www.docker.com/)
- [Python 3.13+](https://www.python.org/) + Gerenciador [`uv`](https://github.com/astral-sh/uv) (Opcional, caso queira rodar fora do Docker)
- [Node.js 20+](https://nodejs.org/) + npm (Opcional)

---

### 🐳 Opção 1: Inicialização via Docker (Recomendado)

**1. Clonar o repositório:**

```bash
git clone <url-do-repositorio>
cd todolist-app

```

**2. Configurar as variáveis de ambiente:**

```bash
cp backend/.env.example backend/.env

```

> ⚠️ **Importante**: Abra o arquivo `.env` gerado e insira uma hash robusta na variável `SECRET_KEY`.

**3. Iniciar a infraestrutura:**

```bash
docker compose up -d

```

**4. Aplicar as migrações do banco de dados:**

```bash
docker compose run --rm api alembic upgrade head

```

**5. Criar uma conta de Administrador (Opcional):**

```bash
docker compose run --rm api python -c "
from app.scripts import create_superuser
import asyncio
asyncio.run(create_superuser('admin', 'admin@email.com', 'Admin@123'))
"

```

#### Portas de Acesso Local:

- **Interface Frontend:** `http://localhost:5173`
- **Servidor Backend (API):** `http://localhost:8000`
- **Documentação Interativa (Swagger):** `http://localhost:8000/docs`

---

### 🐍 Opção 2: Inicialização Manual (Apenas Backend)

Certifique-se de possuir uma instância do **PostgreSQL 17** rodando localmente na porta `5432`.

```bash
cd backend

# Instalar dependências e sincronizar ambiente virtual via uv
uv sync

# Ativar o ambiente virtual
source .venv/bin/activate  # No Linux/macOS
# ou: .venv\Scripts\activate  # No Windows

# Executar migrações (Defina as variáveis no ambiente ou no arquivo .env)
DATABASE_URL="postgresql+asyncpg://user:pass@localhost:5432/db" alembic upgrade head

# Iniciar o servidor de desenvolvimento
uvicorn app.main:app --reload

```

---

## 🛠️ Comandos de Desenvolvimento Úteis

Caso possua o gerenciador de tarefas `just` instalado, você pode executar atalhos rápidos como `just migrate`, `just build` ou `just up`. Caso contrário, utilize os comandos nativos abaixo:

### 🖥️ Operações no Backend

```bash
cd backend
uv run ruff check src tests          # Executa o linter de código
uv run ruff format --check src tests # Valida a formatação do código
uv run pyright                       # Executa a checagem estática de tipos
uv run pytest tests/ --cov=app       # Roda a suíte de testes com relatório de cobertura

```

### 🎨 Operações no Frontend

```bash
cd frontend
npm ci --frozen-lockfile             # Instalação limpa de dependências
npm run dev                          # Inicializa o servidor Vite local
npm run build                        # Compila o projeto compilando tipos TypeScript
npm run lint                         # Executa o linter do ESLint
npx tsc -b                           # Executa estritamente a checagem de tipos

```

---

## 🔑 Variáveis de Ambiente

Configurações disponíveis em `backend/.env.example`:

| Variável                      | Obrigatória | Padrão        | Descrição                                                                |
| ----------------------------- | ----------- | ------------- | ------------------------------------------------------------------------ |
| `SECRET_KEY`                  | ✅ Sim      | —             | Chave de assinatura criptográfica dos tokens JWT.                        |
| `DATABASE_URL`                | ✅ Sim      | —             | String de conexão assíncrona do PostgreSQL (`postgresql+asyncpg://...`). |
| `ALEMBIC_DATABASE_URL`        | ✅ Sim      | —             | String de conexão síncrona usada para migrações (`postgresql://...`).    |
| `ALGORITHM`                   | ❌ Não      | `HS256`       | Algoritmo de criptografia do token JWT.                                  |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | ❌ Não      | `30`          | Tempo de vida (em minutos) do token de acesso.                           |
| `REFRESH_TOKEN_EXPIRE_DAYS`   | ❌ Não      | `7`           | Tempo de vida (em dias) do token de renovação.                           |
| `ENVIRONMENT`                 | ❌ Não      | `development` | Define o estágio da aplicação (`development` ou `production`).           |
| `LOG_LEVEL`                   | ❌ Não      | `INFO`        | Nível mínimo dos logs emitidos pela aplicação.                           |
| `ALLOWED_ORIGINS`             | ❌ Não      | —             | Array JSON contendo as origens permitidas no CORS.                       |
| `TRUSTED_HOSTS`               | ❌ Não      | —             | Array JSON contendo os domínios permitidos no proxy.                     |
| `RATE_LIMIT_*`                | ❌ Não      | `100000/min`  | Chaves customizadas para controle e limitação de requisições.            |

> 🔒 **Política de Senhas:** O sistema rejeitará cadastros que não sigam os critérios mínimos de segurança: Mínimo de 8 caracteres, contendo ao menos 1 letra maiúscula, 1 letra minúscula, 1 número e 1 caractere especial.

---

## 📑 Visão Geral da API (Endpoints principais)

### 👥 Autenticação & Perfil de Usuário

- `POST /auth/register` — Cadastro de novas contas.
- `POST /auth/token` — Autenticação de usuário (Gera cookie HTTPOnly e token de acesso).
- `POST /auth/refresh` — Rotação automática e renovação de sessão.
- `POST /auth/revoke_token` — Logout seguro (Invalida o token de atualização).
- `GET | PATCH | DELETE /users/me` — Gerenciamento do perfil autenticado.

### 📋 Gerenciamento de Tarefas (Todos)

- `GET /todos/` — Listagem paginada com suporte a filtros dinâmicos de busca.
- `POST /todos/` — Criação de novas tarefas.
- `GET | PATCH | DELETE /todos/{uuid}` — Operações individuais em tarefas baseado no identificador único.

### 🛡️ Módulo Administrativo (Restrito)

- `GET | PATCH | DELETE /admin/users/{uuid?}` — Gerenciamento total de contas de usuários.
- `GET | PATCH | DELETE /admin/todos/{uuid?}` — Auditoria global de tarefas do sistema.
- `GET | PATCH | DELETE /admin/tokens/{id?}` — Monitoramento e revogação forçada de sessões ativas.

_Para consultar detalhes de payloads de entrada e formatos de resposta, acesse a documentação do Swagger em `/docs` com o servidor ativo._

---

## 🔄 Integração Contínua (CI/CD)

O projeto conta com um fluxo automatizado via **GitHub Actions** em cada _Pull Request_ ou _Push_ para os ramos principais:

1. **Job de Lint:** Validação estilística e formatação com `ruff` (Backend) e `eslint` + `tsc` (Frontend).
2. **Job de Testes:** Inicialização de banco de dados temporário PostgreSQL via GitHub Services e execução de 161 testes automatizados garantindo **100% de cobertura** das rotas e regras de negócio do backend.
3. **Job de Build:** Execução do build das imagens Docker multi-stage validando a integridade dos artefatos finais de produção.

---

Desenvolvido sob a licença **MIT**.

```

```
