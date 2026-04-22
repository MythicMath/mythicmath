# MythicMath Backend

Guia rapido para o time de front rodar o backend **com Docker** ou **com venv**.

## Requisitos
- Docker Desktop (opcao 1)
- OU Python 3.8+ (opcao 2)

---

## Opcao 1: Rodar com Docker (API + Postgres + Redis)

```powershell
cd C:\Users\user\Downloads\mythicmath\backend
docker compose up -d
docker compose run --rm api alembic upgrade head
```

Pronto. A API fica em `http://127.0.0.1:8000`.

Abrir:
- Docs: `http://127.0.0.1:8000/docs`
- Health: `http://127.0.0.1:8000/health`
- WebSocket: `ws://127.0.0.1:8000/ws`

---

## Opcao 2: Rodar com venv (SQLite local)

```powershell
cd C:\Users\user\Downloads\mythicmath\backend
python -m venv .venv
.\.venv\Scripts\pip install -r requirements.txt

$env:DATABASE_URL="sqlite+aiosqlite:///./dev.db"
.\.venv\Scripts\alembic.exe upgrade head

$env:DATABASE_URL="sqlite+aiosqlite:///./dev.db"
.\.venv\Scripts\uvicorn app.main:app --reload
```

Pronto. A API fica em `http://127.0.0.1:8000`.

---

## Endpoints principais

### Register
`POST /register`

Body:
```json
{ "username": "Ana", "email": "ana@email.com", "password": "123456" }
```

Response:
```json
{ "id": 1, "username": "Ana", "email": "ana@email.com", "token": "..." }
```

### Login
`POST /login`

Body (identifier = email OU username):
```json
{ "identifier": "ana@email.com", "password": "123456" }
```
ou
```json
{ "identifier": "Ana", "password": "123456" }
```

Response:
```json
{ "id": 1, "username": "Ana", "email": "ana@email.com", "token": "..." }
```

### Login com Google
`POST /login/google`

O backend nao faz o login visual do Google. Ele recebe um `id_token` gerado pelo Google no front-end ou no Postman, valida esse token e devolve o token da API MythicMath.

#### 1. Criar o OAuth Client no Google

No Google Cloud Console:

1. Abra `https://console.cloud.google.com/apis/credentials`.
2. Selecione o projeto correto.
3. Clique em `Criar credenciais` > `ID do cliente OAuth`.
4. Escolha `Aplicativo da Web`.
5. Em `URIs de redirecionamento autorizados`, adicione os callbacks usados pelo Postman:

```text
https://oauth.pstmn.io/v1/browser-callback
https://oauth.pstmn.io/v1/callback
https://oauth.pstmn.io/v1/vscode-callback
```

6. Clique em `Criar`.
7. Copie o `ID do cliente`.
8. Copie o `Segredo do cliente` apenas para usar no Postman.

O `Segredo do cliente` costuma comecar com `GOCSPX-`. Se o Google nao mostrar um segredo, provavelmente o client foi criado com outro tipo. Para testar no Postman, use `Aplicativo da Web`.

#### 2. Configurar o backend

Coloque o `ID do cliente` no `.env`:

```env
GOOGLE_CLIENT_IDS=seu-client-id.apps.googleusercontent.com
```

Se o app tiver mais de um Client ID, separe por virgula:

```env
GOOGLE_CLIENT_IDS=web-client-id.apps.googleusercontent.com,android-client-id.apps.googleusercontent.com
```

O backend usa somente o `ID do cliente`. Nao coloque o `Segredo do cliente` no backend para esse fluxo.

Sem Docker, um exemplo de execucao local:

```powershell
cd C:\Users\user\Documents\mythicmath\backend
.\.venv\Scripts\Activate.ps1
$env:DATABASE_URL="sqlite+aiosqlite:///./dev.db"
$env:GOOGLE_CLIENT_IDS="seu-client-id.apps.googleusercontent.com"
alembic upgrade head
uvicorn app.main:app --reload
```

#### 3. Gerar o id_token no Postman

No Postman, crie uma request qualquer e abra a aba `Authorization`.

Preencha:

```text
Type: OAuth 2.0
```

Em `Configure New Token`, use:

```text
Token Name: google-login
Grant Type: Authorization Code
Callback URL: use o callback que o Postman mostrar
Auth URL: https://accounts.google.com/o/oauth2/v2/auth
Access Token URL: https://oauth2.googleapis.com/token
Client ID: seu-client-id.apps.googleusercontent.com
Client Secret: seu-client-secret
Scope: openid email profile
State: teste123
Client Authentication: Send client credentials in body
```

O `Callback URL` precisa ser exatamente igual a um dos redirects cadastrados no Google Cloud. No Postman normal, geralmente e:

```text
https://oauth.pstmn.io/v1/browser-callback
```

No Postman dentro do VS Code, pode ser:

```text
https://oauth.pstmn.io/v1/vscode-callback
```

Clique em `Get New Access Token`, faca login no Google e autorize.

Depois de gerar o token, abra os detalhes em `Manage Tokens`, `Available Tokens`, `Token Response` ou `Raw Response`, dependendo da versao do Postman.

Copie o campo:

```text
id_token
```

O `id_token` geralmente comeca com:

```text
eyJ
```

Nao use o `access_token`. O `access_token` costuma comecar com `ya29` e nao e o valor esperado pelo endpoint `/login/google`.

Se o Postman mostrar `Access Token: google-login`, isso nao e um token real. Nesse caso, o texto `google-login` foi colocado no campo errado ou o token nao foi gerado pelo fluxo OAuth.

#### 4. Testar o endpoint /login/google

No endpoint `/login/google`, nao use `Params`. Use `Body`.

Request:

```text
POST http://127.0.0.1:8000/login/google
```

Headers:

```text
Content-Type: application/json
```

Body > raw > JSON:

```json
{ "id_token": "cole-aqui-o-id-token" }
```

Tambem aceita o nome usado pelo Google Identity Services Web:

```json
{ "credential": "cole-aqui-o-id-token" }
```

Response:

```json
{ "id": 1, "username": "Ana", "email": "ana@email.com", "token": "..." }
```

Erros comuns:

- `redirect_uri_mismatch`: o Callback URL do Postman nao esta igual ao redirect cadastrado no Google Cloud.
- `GOOGLE_CLIENT_IDS is not configured`: a variavel `GOOGLE_CLIENT_IDS` nao foi configurada ou o backend nao foi reiniciado.
- `Invalid Google ID token`: o token expirou, nao e um `id_token`, ou foi gerado para outro Client ID.
- Coluna `google_sub` nao existe: rode `alembic upgrade head`.

### Logout
`POST /logout`

Body:
```json
{ "token": "..." }
```

Response:
```json
{ "success": true }
```

---

## Observacao
- Docker usa o `.env` local automaticamente.
- venv usa SQLite (`dev.db`) e nao precisa de Postgres/Redis.
