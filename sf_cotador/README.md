# SF COTADOR

Projeto inicial para evolução do sistema de cotação, com tela base simples.

## Banco de dados

O projeto agora suporta dois backends:

- `sqlite` (padrao)
- `access` (Microsoft Access `.mdb/.accdb` via ODBC)

### Backend SQLite (padrao)

- SQLite local em `sf_cotador/data/sf_cotador.db`
- Tabela `TB_COT_CAD_FORNEC`
  - Campos: `ID (INTEGER)`, `Procfit (INTEGER)`, `Nome (TEXT)`, `Nome Fantasia (TEXT)`
- Tabela `TB_COT_CAD_REPRESENTANTE`
  - Campos: `CodRepres (INTEGER)`, `Nome (TEXT)`, `Login (TEXT/e-mail)`, `Cod Forn (INTEGER)`, `Fornecedor (TEXT)`, `Cod Marca (INTEGER)`, `Marca (TEXT)`
- Tabela `TB_COT_CONTATO`
  - Campos: `D (INTEGER)`, `Nome (TEXT)`, `E-mail/Usuario (TEXT)`, `Situacao (Ativo/Inativo)`, `Acoes (TEXT)`

Chaves primarias:

- `TB_COT_CAD_FORNEC`: `(ID, Procfit)`
- `TB_COT_CAD_REPRESENTANTE`: `(CodRepres, Cod Forn, Cod Marca)`
- `TB_COT_CONTATO`: `D`

### Backend Access (fase de integracao)

1. Instale `pyodbc`:

```powershell
python -m pip install pyodbc
```

2. Garanta o driver ODBC do Access instalado no Windows:

- `Microsoft Access Driver (*.mdb, *.accdb)`

3. Configure variaveis de ambiente e execute:

```powershell
$env:SF_COTADOR_DB_BACKEND = "access"
$env:SF_COTADOR_ACCESS_FILE = "C:\caminho\seu_banco.accdb"
python .\main.py
```

Opcional: usar string de conexao pronta:

```powershell
$env:SF_COTADOR_DB_BACKEND = "access"
$env:SF_COTADOR_ACCESS_CONN_STR = "DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};DBQ=C:\caminho\seu_banco.accdb;"
python .\main.py
```

Opcional: driver customizado:

```powershell
$env:SF_COTADOR_ACCESS_DRIVER = "Microsoft Access Driver (*.mdb, *.accdb)"
```

## Fluxo atual

- A coluna `Ações` na tela principal está reservada para novas funcionalidades.
- Os botões `Fornecedores`, `Representantes` e `Contatos` abrem formulários suspensos (janela modal) para digitação e gravação dos dados.

## Requisitos

- Python 3.11+

## Executar localmente

No PowerShell, dentro da pasta `sf_cotador`:

```powershell
python .\main.py
```

## Gerar executável (instalar)

1. Instale o PyInstaller:

```powershell
python -m pip install pyinstaller
```

2. Gere o `.exe`:

```powershell
pyinstaller --noconfirm --onefile --windowed --name "SF_COTADOR" .\main.py
```

3. O executável será criado em:

`sf_cotador\dist\SF_COTADOR.exe`

## Instruções para commit

Se o repositório Git estiver configurado na máquina:

```powershell
git add sf_cotador/main.py sf_cotador/database.py sf_cotador/README.md
git commit -m "feat: adiciona banco interno e lista de fornecedores"
```

> Observação: neste ambiente, o comando `git` não está disponível no PATH.
