import os
import sqlite3
from pathlib import Path
from typing import Any, Protocol

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "sf_cotador.db"

TABLE_FORNEC = "TB_COT_CAD_FORNEC"
TABLE_REPRES = "TB_COT_CAD_REPRESENTANTE"
TABLE_CONTATO = "TB_COT_CONTATO"

LEGACY_TABLE_MARCAS = "dbo.MARCAS"
LEGACY_TABLE_PRODUTOS = "dbo.PRODUTOS"
LEGACY_TABLE_PRODUTOS_EAN = "dbo.PRODUTOS_EAN"
LEGACY_TABLE_PRODUTOS_FORNECEDORES = "dbo.PRODUTOS_FORNECEDORES"
LEGACY_TABLE_ESTOQUE_DEMANDAS = "dbo.VW_PRODUTOS_ESTOQUE_DEMANDAS"

DEFAULT_SQL_SERVER_DRIVER = "ODBC Driver 18 for SQL Server"
DEFAULT_SQL_SERVER_HOST = "rosario.procfit.com.br"
DEFAULT_SQL_SERVER_PORT = "1433"
DEFAULT_SQL_SERVER_DATABASE = "PBS_ROSARIO_DADOS"
DEFAULT_SQL_SERVER_USER = "rosario.ServiceFarma"
DEFAULT_SQL_SERVER_PASSWORD = "gtujku"


class DatabaseAdapter(Protocol):
    def init_db(self) -> None: ...
    def fetch_fornecedores(self) -> list[dict[str, Any]]: ...
    def insert_fornecedor(self, id_fornec: int, procfit: int, nome: str, nome_fantasia: str) -> None: ...
    def fetch_representantes(self) -> list[dict[str, Any]]: ...
    def insert_representante(
        self,
        cod_repres: int,
        nome: str,
        login: str,
        cod_forn: int,
        fornecedor: str,
        cod_marca: int,
        marca: str,
    ) -> None: ...
    def fetch_contatos(self) -> list[dict[str, Any]]: ...
    def insert_contato(self, d_contato: int, nome: str, email_usuario: str, situacao: str, acoes: str) -> None: ...
    def fetch_relatorio_contatos(self) -> list[dict[str, Any]]: ...


class SQLiteAdapter:
    def get_connection(self) -> sqlite3.Connection:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self) -> None:
        with self.get_connection() as conn:
            self._ensure_fornecedor_schema(conn)
            self._ensure_representante_schema(conn)
            self._ensure_contato_schema(conn)
            self._seed_data(conn)

    def _ensure_fornecedor_schema(self, conn: sqlite3.Connection) -> None:
        conn.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {TABLE_FORNEC} (
                ID INTEGER NOT NULL,
                Procfit INTEGER NOT NULL,
                Nome TEXT NOT NULL,
                "Nome Fantasia" TEXT NOT NULL,
                PRIMARY KEY (ID, Procfit)
            )
            """
        )
        cols = conn.execute(f"PRAGMA table_info({TABLE_FORNEC})").fetchall()
        col_names = {r["name"] for r in cols}
        if col_names == {"ID", "Procfit", "Nome", "Nome Fantasia"} and sum(1 for r in cols if r["pk"]) == 2:
            return

        conn.execute(f"ALTER TABLE {TABLE_FORNEC} RENAME TO {TABLE_FORNEC}_OLD")
        conn.execute(
            f"""
            CREATE TABLE {TABLE_FORNEC} (
                ID INTEGER NOT NULL,
                Procfit INTEGER NOT NULL,
                Nome TEXT NOT NULL,
                "Nome Fantasia" TEXT NOT NULL,
                PRIMARY KEY (ID, Procfit)
            )
            """
        )
        conn.execute(
            f"""
            INSERT OR IGNORE INTO {TABLE_FORNEC} (ID, Procfit, Nome, "Nome Fantasia")
            SELECT
                CAST(ID AS INTEGER),
                CAST(Procfit AS INTEGER),
                Nome,
                CASE
                    WHEN "Nome Fantasia" IS NULL OR TRIM("Nome Fantasia") = '' THEN Nome
                    ELSE "Nome Fantasia"
                END
            FROM {TABLE_FORNEC}_OLD
            """
        )
        conn.execute(f"DROP TABLE {TABLE_FORNEC}_OLD")
        conn.commit()

    def _ensure_representante_schema(self, conn: sqlite3.Connection) -> None:
        conn.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {TABLE_REPRES} (
                CodRepres INTEGER NOT NULL,
                Nome TEXT NOT NULL,
                Login TEXT NOT NULL,
                "Cod Forn" INTEGER NOT NULL,
                Fornecedor TEXT NOT NULL,
                "Cod Marca" INTEGER NOT NULL,
                Marca TEXT NOT NULL,
                PRIMARY KEY (CodRepres, "Cod Forn", "Cod Marca")
            )
            """
        )
        cols = conn.execute(f"PRAGMA table_info({TABLE_REPRES})").fetchall()
        col_names = {r["name"] for r in cols}
        if col_names == {"CodRepres", "Nome", "Login", "Cod Forn", "Fornecedor", "Cod Marca", "Marca"} and sum(
            1 for r in cols if r["pk"]
        ) == 3:
            return

        conn.execute(f"ALTER TABLE {TABLE_REPRES} RENAME TO {TABLE_REPRES}_OLD")
        conn.execute(
            f"""
            CREATE TABLE {TABLE_REPRES} (
                CodRepres INTEGER NOT NULL,
                Nome TEXT NOT NULL,
                Login TEXT NOT NULL,
                "Cod Forn" INTEGER NOT NULL,
                Fornecedor TEXT NOT NULL,
                "Cod Marca" INTEGER NOT NULL,
                Marca TEXT NOT NULL,
                PRIMARY KEY (CodRepres, "Cod Forn", "Cod Marca")
            )
            """
        )
        conn.execute(
            f"""
            INSERT OR IGNORE INTO {TABLE_REPRES}
                (CodRepres, Nome, Login, "Cod Forn", Fornecedor, "Cod Marca", Marca)
            SELECT
                CAST(CodRepres AS INTEGER),
                Nome,
                Login,
                CAST("Cod Forn" AS INTEGER),
                Fornecedor,
                CAST("Cod Marca" AS INTEGER),
                Marca
            FROM {TABLE_REPRES}_OLD
            """
        )
        conn.execute(f"DROP TABLE {TABLE_REPRES}_OLD")
        conn.commit()

    def _ensure_contato_schema(self, conn: sqlite3.Connection) -> None:
        conn.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {TABLE_CONTATO} (
                D INTEGER PRIMARY KEY,
                Nome TEXT NOT NULL,
                "E-mail/Usuario" TEXT NOT NULL,
                Situacao TEXT NOT NULL CHECK(Situacao IN ('Ativo', 'Inativo')),
                Acoes TEXT NOT NULL
            )
            """
        )
        cols = conn.execute(f"PRAGMA table_info({TABLE_CONTATO})").fetchall()
        col_names = {r["name"] for r in cols}
        if col_names == {"D", "Nome", "E-mail/Usuario", "Situacao", "Acoes"}:
            return

        conn.execute(f"ALTER TABLE {TABLE_CONTATO} RENAME TO {TABLE_CONTATO}_OLD")
        conn.execute(
            f"""
            CREATE TABLE {TABLE_CONTATO} (
                D INTEGER PRIMARY KEY,
                Nome TEXT NOT NULL,
                "E-mail/Usuario" TEXT NOT NULL,
                Situacao TEXT NOT NULL CHECK(Situacao IN ('Ativo', 'Inativo')),
                Acoes TEXT NOT NULL
            )
            """
        )
        old_cols = {r["name"] for r in conn.execute(f"PRAGMA table_info({TABLE_CONTATO}_OLD)").fetchall()}
        id_col = "D" if "D" in old_cols else "ID"
        conn.execute(
            f"""
            INSERT OR IGNORE INTO {TABLE_CONTATO} (D, Nome, "E-mail/Usuario", Situacao, Acoes)
            SELECT
                CAST({id_col} AS INTEGER),
                Nome,
                "E-mail/Usuario",
                CASE WHEN Situacao IN ('Ativo', 'Inativo') THEN Situacao ELSE 'Ativo' END,
                COALESCE(Acoes, '')
            FROM {TABLE_CONTATO}_OLD
            """
        )
        conn.execute(f"DROP TABLE {TABLE_CONTATO}_OLD")
        conn.commit()

    def _seed_data(self, conn: sqlite3.Connection) -> None:
        cur = conn.cursor()
        cur.execute(f"SELECT COUNT(*) FROM {TABLE_FORNEC}")
        if cur.fetchone()[0] == 0:
            cur.execute(
                f"""
                INSERT INTO {TABLE_FORNEC} (ID, Procfit, Nome, "Nome Fantasia")
                VALUES (?, ?, ?, ?)
                """,
                (1, 3628, "ANDORINHA COMERCIO E DISTRIBUICAO LTDA", "ANDORINHA"),
            )

        cur.execute(f"SELECT COUNT(*) FROM {TABLE_REPRES}")
        if cur.fetchone()[0] == 0:
            cur.execute(
                f"""
                INSERT INTO {TABLE_REPRES}
                    (CodRepres, Nome, Login, "Cod Forn", Fornecedor, "Cod Marca", Marca)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    285,
                    "Andrey Boter",
                    "andrey.boter@hotmail.com",
                    3134069,
                    "CONFORT BRASIL SP LTDA - EPP",
                    497,
                    "ABOVE BASTON",
                ),
            )

        cur.execute(f"SELECT COUNT(*) FROM {TABLE_CONTATO}")
        if cur.fetchone()[0] == 0:
            cur.execute(
                f"""
                INSERT INTO {TABLE_CONTATO} (D, Nome, "E-mail/Usuario", Situacao, Acoes)
                VALUES (?, ?, ?, ?, ?)
                """,
                (222, "Vanessa", "disk.descartaveis@terra.com.br", "Ativo", "Contato inicial"),
            )
        conn.commit()

    def fetch_fornecedores(self) -> list[dict[str, Any]]:
        with self.get_connection() as conn:
            cur = conn.execute(
                f"""
                SELECT ID, Procfit, Nome, "Nome Fantasia"
                FROM {TABLE_FORNEC}
                ORDER BY ID, Procfit
                """
            )
            return [dict(row) for row in cur.fetchall()]

    def insert_fornecedor(self, id_fornec: int, procfit: int, nome: str, nome_fantasia: str) -> None:
        with self.get_connection() as conn:
            conn.execute(
                f"""
                INSERT OR REPLACE INTO {TABLE_FORNEC} (ID, Procfit, Nome, "Nome Fantasia")
                VALUES (?, ?, ?, ?)
                """,
                (id_fornec, procfit, nome, nome_fantasia),
            )
            conn.commit()

    def fetch_representantes(self) -> list[dict[str, Any]]:
        with self.get_connection() as conn:
            cur = conn.execute(
                f"""
                SELECT CodRepres, Nome, Login, "Cod Forn", Fornecedor, "Cod Marca", Marca
                FROM {TABLE_REPRES}
                ORDER BY CodRepres, "Cod Forn", "Cod Marca"
                """
            )
            return [dict(row) for row in cur.fetchall()]

    def insert_representante(
        self,
        cod_repres: int,
        nome: str,
        login: str,
        cod_forn: int,
        fornecedor: str,
        cod_marca: int,
        marca: str,
    ) -> None:
        with self.get_connection() as conn:
            conn.execute(
                f"""
                INSERT OR REPLACE INTO {TABLE_REPRES}
                    (CodRepres, Nome, Login, "Cod Forn", Fornecedor, "Cod Marca", Marca)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (cod_repres, nome, login, cod_forn, fornecedor, cod_marca, marca),
            )
            conn.commit()

    def fetch_contatos(self) -> list[dict[str, Any]]:
        with self.get_connection() as conn:
            cur = conn.execute(
                f"""
                SELECT D, Nome, "E-mail/Usuario", Situacao, Acoes
                FROM {TABLE_CONTATO}
                ORDER BY D
                """
            )
            return [dict(row) for row in cur.fetchall()]

    def insert_contato(self, d_contato: int, nome: str, email_usuario: str, situacao: str, acoes: str) -> None:
        with self.get_connection() as conn:
            conn.execute(
                f"""
                INSERT OR REPLACE INTO {TABLE_CONTATO} (D, Nome, "E-mail/Usuario", Situacao, Acoes)
                VALUES (?, ?, ?, ?, ?)
                """,
                (d_contato, nome, email_usuario, situacao, acoes),
            )
            conn.commit()

    def fetch_relatorio_contatos(self) -> list[dict[str, Any]]:
        with self.get_connection() as conn:
            cur = conn.execute(
                f"""
                SELECT
                    c.D,
                    c.Nome AS Contato,
                    c."E-mail/Usuario",
                    c.Situacao,
                    c.Acoes,
                    r.CodRepres,
                    r.Nome AS Representante,
                    r.Login,
                    r."Cod Forn",
                    r.Fornecedor,
                    r."Cod Marca",
                    r.Marca,
                    f.ID AS FornecedorID,
                    f.Procfit,
                    f.Nome AS Fabricante,
                    f."Nome Fantasia"
                FROM {TABLE_CONTATO} AS c
                INNER JOIN {TABLE_REPRES} AS r
                    ON c.D = r.CodRepres
                INNER JOIN {TABLE_FORNEC} AS f
                    ON r."Cod Forn" = f.Procfit
                ORDER BY f.Nome, r.Marca, c.Nome, c.D
                """
            )
            return [dict(row) for row in cur.fetchall()]


class AccessAdapter:
    def __init__(self) -> None:
        self.conn_str = self._build_connection_string()

    def _build_connection_string(self) -> str:
        direct = os.getenv("SF_COTADOR_ACCESS_CONN_STR", "").strip()
        if direct:
            return direct

        access_file = os.getenv("SF_COTADOR_ACCESS_FILE", "").strip()
        if not access_file:
            raise RuntimeError(
                "Backend Access ativo, mas SF_COTADOR_ACCESS_FILE ou SF_COTADOR_ACCESS_CONN_STR nao foi informado."
            )
        file_path = Path(access_file).expanduser().resolve()
        if not file_path.exists():
            raise RuntimeError(f"Arquivo Access nao encontrado: {file_path}")

        driver = os.getenv("SF_COTADOR_ACCESS_DRIVER", "Microsoft Access Driver (*.mdb, *.accdb)")
        return f"DRIVER={{{driver}}};DBQ={file_path};"

    def _connect(self):
        try:
            import pyodbc
        except ImportError as exc:
            raise RuntimeError(
                "pyodbc nao esta instalado. Instale com: python -m pip install pyodbc"
            ) from exc
        return pyodbc.connect(self.conn_str)

    def _create_table_if_missing(self, conn, table: str, ddl: str) -> None:
        cur = conn.cursor()
        try:
            cur.execute(f"SELECT TOP 1 * FROM [{table}]")
        except Exception:
            cur.execute(ddl)
            conn.commit()

    def _row_to_dicts(self, cursor) -> list[dict[str, Any]]:
        cols = [c[0] for c in cursor.description]
        return [dict(zip(cols, row)) for row in cursor.fetchall()]

    def init_db(self) -> None:
        with self._connect() as conn:
            self._create_table_if_missing(
                conn,
                TABLE_FORNEC,
                f"""
                CREATE TABLE [{TABLE_FORNEC}] (
                    [ID] LONG NOT NULL,
                    [Procfit] LONG NOT NULL,
                    [Nome] TEXT(255) NOT NULL,
                    [Nome Fantasia] TEXT(255) NOT NULL,
                    CONSTRAINT [PK_{TABLE_FORNEC}] PRIMARY KEY ([ID], [Procfit])
                )
                """,
            )
            self._create_table_if_missing(
                conn,
                TABLE_REPRES,
                f"""
                CREATE TABLE [{TABLE_REPRES}] (
                    [CodRepres] LONG NOT NULL,
                    [Nome] TEXT(255) NOT NULL,
                    [Login] TEXT(255) NOT NULL,
                    [Cod Forn] LONG NOT NULL,
                    [Fornecedor] TEXT(255) NOT NULL,
                    [Cod Marca] LONG NOT NULL,
                    [Marca] TEXT(255) NOT NULL,
                    CONSTRAINT [PK_{TABLE_REPRES}] PRIMARY KEY ([CodRepres], [Cod Forn], [Cod Marca])
                )
                """,
            )
            self._create_table_if_missing(
                conn,
                TABLE_CONTATO,
                f"""
                CREATE TABLE [{TABLE_CONTATO}] (
                    [D] LONG NOT NULL,
                    [Nome] TEXT(255) NOT NULL,
                    [E-mail/Usuario] TEXT(255) NOT NULL,
                    [Situacao] TEXT(20) NOT NULL,
                    [Acoes] TEXT(255) NOT NULL,
                    CONSTRAINT [PK_{TABLE_CONTATO}] PRIMARY KEY ([D])
                )
                """,
            )

    def fetch_fornecedores(self) -> list[dict[str, Any]]:
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute(
                f"""
                SELECT [ID], [Procfit], [Nome], [Nome Fantasia]
                FROM [{TABLE_FORNEC}]
                ORDER BY [ID], [Procfit]
                """
            )
            return self._row_to_dicts(cur)

    def insert_fornecedor(self, id_fornec: int, procfit: int, nome: str, nome_fantasia: str) -> None:
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute(
                f"SELECT COUNT(*) FROM [{TABLE_FORNEC}] WHERE [ID]=? AND [Procfit]=?",
                (id_fornec, procfit),
            )
            exists = cur.fetchone()[0] > 0
            if exists:
                cur.execute(
                    f"""
                    UPDATE [{TABLE_FORNEC}]
                    SET [Nome]=?, [Nome Fantasia]=?
                    WHERE [ID]=? AND [Procfit]=?
                    """,
                    (nome, nome_fantasia, id_fornec, procfit),
                )
            else:
                cur.execute(
                    f"""
                    INSERT INTO [{TABLE_FORNEC}] ([ID], [Procfit], [Nome], [Nome Fantasia])
                    VALUES (?, ?, ?, ?)
                    """,
                    (id_fornec, procfit, nome, nome_fantasia),
                )
            conn.commit()

    def fetch_representantes(self) -> list[dict[str, Any]]:
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute(
                f"""
                SELECT [CodRepres], [Nome], [Login], [Cod Forn], [Fornecedor], [Cod Marca], [Marca]
                FROM [{TABLE_REPRES}]
                ORDER BY [CodRepres], [Cod Forn], [Cod Marca]
                """
            )
            return self._row_to_dicts(cur)

    def insert_representante(
        self,
        cod_repres: int,
        nome: str,
        login: str,
        cod_forn: int,
        fornecedor: str,
        cod_marca: int,
        marca: str,
    ) -> None:
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute(
                f"""
                SELECT COUNT(*)
                FROM [{TABLE_REPRES}]
                WHERE [CodRepres]=? AND [Cod Forn]=? AND [Cod Marca]=?
                """,
                (cod_repres, cod_forn, cod_marca),
            )
            exists = cur.fetchone()[0] > 0
            if exists:
                cur.execute(
                    f"""
                    UPDATE [{TABLE_REPRES}]
                    SET [Nome]=?, [Login]=?, [Fornecedor]=?, [Marca]=?
                    WHERE [CodRepres]=? AND [Cod Forn]=? AND [Cod Marca]=?
                    """,
                    (nome, login, fornecedor, marca, cod_repres, cod_forn, cod_marca),
                )
            else:
                cur.execute(
                    f"""
                    INSERT INTO [{TABLE_REPRES}]
                        ([CodRepres], [Nome], [Login], [Cod Forn], [Fornecedor], [Cod Marca], [Marca])
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (cod_repres, nome, login, cod_forn, fornecedor, cod_marca, marca),
                )
            conn.commit()

    def fetch_contatos(self) -> list[dict[str, Any]]:
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute(
                f"""
                SELECT [D], [Nome], [E-mail/Usuario], [Situacao], [Acoes]
                FROM [{TABLE_CONTATO}]
                ORDER BY [D]
                """
            )
            return self._row_to_dicts(cur)

    def insert_contato(self, d_contato: int, nome: str, email_usuario: str, situacao: str, acoes: str) -> None:
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute(f"SELECT COUNT(*) FROM [{TABLE_CONTATO}] WHERE [D]=?", (d_contato,))
            exists = cur.fetchone()[0] > 0
            if exists:
                cur.execute(
                    f"""
                    UPDATE [{TABLE_CONTATO}]
                    SET [Nome]=?, [E-mail/Usuario]=?, [Situacao]=?, [Acoes]=?
                    WHERE [D]=?
                    """,
                    (nome, email_usuario, situacao, acoes, d_contato),
                )
            else:
                cur.execute(
                    f"""
                    INSERT INTO [{TABLE_CONTATO}] ([D], [Nome], [E-mail/Usuario], [Situacao], [Acoes])
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (d_contato, nome, email_usuario, situacao, acoes),
                )
            conn.commit()

    def fetch_relatorio_contatos(self) -> list[dict[str, Any]]:
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute(
                f"""
                SELECT
                    c.[D],
                    c.[Nome] AS [Contato],
                    c.[E-mail/Usuario],
                    c.[Situacao],
                    c.[Acoes],
                    r.[CodRepres],
                    r.[Nome] AS [Representante],
                    r.[Login],
                    r.[Cod Forn],
                    r.[Fornecedor],
                    r.[Cod Marca],
                    r.[Marca],
                    f.[ID] AS [FornecedorID],
                    f.[Procfit],
                    f.[Nome] AS [Fabricante],
                    f.[Nome Fantasia]
                FROM ([{TABLE_CONTATO}] AS c
                INNER JOIN [{TABLE_REPRES}] AS r
                    ON c.[D] = r.[CodRepres])
                INNER JOIN [{TABLE_FORNEC}] AS f
                    ON r.[Cod Forn] = f.[Procfit]
                ORDER BY f.[Nome], r.[Marca], c.[Nome], c.[D]
                """
            )
            return self._row_to_dicts(cur)


class LegacySQLServerAdapter:
    def __init__(self) -> None:
        self.conn_str = self._build_connection_string()

    def _build_connection_string(self) -> str:
        direct = os.getenv("SF_COTADOR_LEGACY_SQLSERVER_CONN_STR", "").strip()
        if direct:
            return direct

        server = os.getenv("SF_COTADOR_LEGACY_SQLSERVER_HOST", DEFAULT_SQL_SERVER_HOST).strip()
        if not server:
            raise RuntimeError("SF_COTADOR_LEGACY_SQLSERVER_HOST nao foi informado.")

        port = os.getenv("SF_COTADOR_LEGACY_SQLSERVER_PORT", DEFAULT_SQL_SERVER_PORT).strip()
        database_name = os.getenv("SF_COTADOR_LEGACY_SQLSERVER_DATABASE", DEFAULT_SQL_SERVER_DATABASE).strip()
        if not database_name:
            raise RuntimeError("SF_COTADOR_LEGACY_SQLSERVER_DATABASE nao foi informado.")

        driver = os.getenv("SF_COTADOR_LEGACY_SQLSERVER_DRIVER", DEFAULT_SQL_SERVER_DRIVER).strip()
        username = os.getenv("SF_COTADOR_LEGACY_SQLSERVER_USER", DEFAULT_SQL_SERVER_USER).strip()
        password = os.getenv("SF_COTADOR_LEGACY_SQLSERVER_PASSWORD", DEFAULT_SQL_SERVER_PASSWORD).strip()
        trust_cert = os.getenv("SF_COTADOR_LEGACY_SQLSERVER_TRUST_CERT", "yes").strip().lower()

        server_ref = server if not port else f"{server},{port}"
        conn_parts = [
            f"DRIVER={{{driver}}}",
            f"SERVER={server_ref}",
            f"DATABASE={database_name}",
            f"TrustServerCertificate={trust_cert}",
        ]

        if username:
            conn_parts.append(f"UID={username}")
            conn_parts.append(f"PWD={password}")
        else:
            conn_parts.append("Trusted_Connection=yes")

        return ";".join(conn_parts) + ";"

    def _connect(self):
        try:
            import pyodbc
        except ImportError as exc:
            raise RuntimeError(
                "pyodbc nao esta instalado. Instale com: python -m pip install pyodbc"
            ) from exc
        return pyodbc.connect(self.conn_str)

    def _row_to_dicts(self, cursor) -> list[dict[str, Any]]:
        cols = [c[0] for c in cursor.description]
        return [dict(zip(cols, row)) for row in cursor.fetchall()]

    def _qualify_name(self, object_name: str) -> str:
        parts = [part.strip() for part in object_name.split(".") if part.strip()]
        if not parts:
            raise RuntimeError("Nome de objeto SQL Server invalido.")
        return ".".join(f"[{part}]" for part in parts)

    def fetch_table(self, table_name: str) -> list[dict[str, Any]]:
        allowed_tables = {
            LEGACY_TABLE_MARCAS,
            LEGACY_TABLE_PRODUTOS,
            LEGACY_TABLE_PRODUTOS_EAN,
            LEGACY_TABLE_PRODUTOS_FORNECEDORES,
            LEGACY_TABLE_ESTOQUE_DEMANDAS,
        }
        if table_name not in allowed_tables:
            raise RuntimeError(f"Tabela legada nao permitida: {table_name}")

        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute(f"SELECT * FROM {self._qualify_name(table_name)}")
            return self._row_to_dicts(cur)

    def fetch_produtos_integrados(self) -> list[dict[str, Any]]:
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute(
                f"""
                SELECT
                    p.[PRODUTO] AS [CD_PROD],
                    p.[DESCRICAO],
                    p.[MARCA] AS [CD_MARCA],
                    m.[DESCRICAO] AS [MARCA],
                    e.[EAN]
                FROM {self._qualify_name(LEGACY_TABLE_PRODUTOS_EAN)} AS e
                INNER JOIN {self._qualify_name(LEGACY_TABLE_PRODUTOS)} AS p
                    ON e.[PRODUTO] = p.[PRODUTO]
                INNER JOIN {self._qualify_name(LEGACY_TABLE_MARCAS)} AS m
                    ON m.[MARCA] = p.[MARCA]
                ORDER BY p.[DESCRICAO], e.[EAN]
                """
            )
            return self._row_to_dicts(cur)


def _build_adapter() -> DatabaseAdapter:
    backend = os.getenv("SF_COTADOR_DB_BACKEND", "sqlite").strip().lower()
    if backend == "sqlite":
        return SQLiteAdapter()
    if backend == "access":
        return AccessAdapter()
    raise RuntimeError("SF_COTADOR_DB_BACKEND invalido. Use 'sqlite' ou 'access'.")


_ADAPTER: DatabaseAdapter = _build_adapter()
_LEGACY_ADAPTER: LegacySQLServerAdapter | None = None


def _get_legacy_adapter() -> LegacySQLServerAdapter:
    global _LEGACY_ADAPTER
    if _LEGACY_ADAPTER is None:
        _LEGACY_ADAPTER = LegacySQLServerAdapter()
    return _LEGACY_ADAPTER


def init_db() -> None:
    _ADAPTER.init_db()


def fetch_fornecedores() -> list[dict[str, Any]]:
    return _ADAPTER.fetch_fornecedores()


def insert_fornecedor(id_fornec: int, procfit: int, nome: str, nome_fantasia: str) -> None:
    _ADAPTER.insert_fornecedor(id_fornec, procfit, nome, nome_fantasia)


def fetch_representantes() -> list[dict[str, Any]]:
    return _ADAPTER.fetch_representantes()


def insert_representante(
    cod_repres: int,
    nome: str,
    login: str,
    cod_forn: int,
    fornecedor: str,
    cod_marca: int,
    marca: str,
) -> None:
    _ADAPTER.insert_representante(cod_repres, nome, login, cod_forn, fornecedor, cod_marca, marca)


def fetch_contatos() -> list[dict[str, Any]]:
    return _ADAPTER.fetch_contatos()


def insert_contato(d_contato: int, nome: str, email_usuario: str, situacao: str, acoes: str) -> None:
    _ADAPTER.insert_contato(d_contato, nome, email_usuario, situacao, acoes)


def fetch_relatorio_contatos() -> list[dict[str, Any]]:
    return _ADAPTER.fetch_relatorio_contatos()


def fetch_legado_marcas() -> list[dict[str, Any]]:
    return _get_legacy_adapter().fetch_table(LEGACY_TABLE_MARCAS)


def fetch_legado_produtos() -> list[dict[str, Any]]:
    return _get_legacy_adapter().fetch_table(LEGACY_TABLE_PRODUTOS)


def fetch_legado_produtos_ean() -> list[dict[str, Any]]:
    return _get_legacy_adapter().fetch_table(LEGACY_TABLE_PRODUTOS_EAN)


def fetch_legado_produtos_fornecedores() -> list[dict[str, Any]]:
    return _get_legacy_adapter().fetch_table(LEGACY_TABLE_PRODUTOS_FORNECEDORES)


def fetch_legado_produtos_estoque_demandas() -> list[dict[str, Any]]:
    return _get_legacy_adapter().fetch_table(LEGACY_TABLE_ESTOQUE_DEMANDAS)


def fetch_legado_produtos_integrados() -> list[dict[str, Any]]:
    return _get_legacy_adapter().fetch_produtos_integrados()


def fetch_relatorio_contatos_produtos() -> list[dict[str, Any]]:
    contatos = fetch_relatorio_contatos()
    produtos = fetch_legado_produtos_integrados()

    produtos_por_marca: dict[int, list[dict[str, Any]]] = {}
    for produto in produtos:
        try:
            cod_marca = int(produto["CD_MARCA"])
        except (TypeError, ValueError, KeyError):
            continue
        produtos_por_marca.setdefault(cod_marca, []).append(produto)

    resultado: list[dict[str, Any]] = []
    for contato in contatos:
        try:
            cod_marca = int(contato["Cod Marca"])
        except (TypeError, ValueError, KeyError):
            continue

        for produto in produtos_por_marca.get(cod_marca, []):
            resultado.append(
                {
                    "Nome": contato["Contato"],
                    "E-mail/Usuario": contato["E-mail/Usuario"],
                    "CD_FORNEC": contato["Cod Forn"],
                    "Nome Fantasia": contato["Nome Fantasia"],
                    "MARCA": produto["MARCA"],
                    "CD_PROD": produto["CD_PROD"],
                    "EAN": produto["EAN"],
                    "DESCRICAO": produto["DESCRICAO"],
                    "VALOR UNITARIO": "",
                    "FATOR EMBALAGEM": "",
                }
            )

    resultado.sort(key=lambda row: (str(row["DESCRICAO"]), str(row["Nome"]), str(row["EAN"])))
    return resultado
