import os
import socket
import sqlite3
from pathlib import Path
from typing import Any, Protocol

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "sf_cotador.db"

TABLE_FORNEC = "TB_COT_CAD_FORNEC"
TABLE_REPRES = "TB_COT_CAD_REPRESENTANTE"
TABLE_CONTATO = "TB_COT_CONTATO"
TABLE_COTACAO_CAPTADA = "TB_COT_CAPTURA"
TABLE_CONNECTION_SETTINGS = "TB_COT_CONFIG_CONEXAO"

LEGACY_TABLE_MARCAS = "dbo.MARCAS"
LEGACY_TABLE_PRODUTOS = "dbo.PRODUTOS"
LEGACY_TABLE_PRODUTOS_EAN = "dbo.PRODUTOS_EAN"
LEGACY_TABLE_PRODUTOS_FORNECEDORES = "dbo.PRODUTOS_FORNECEDORES"
LEGACY_TABLE_ESTOQUE_DEMANDAS = "dbo.VW_PRODUTOS_ESTOQUE_DEMANDAS"
LEGACY_QUERY_ULT_CUSTO = "CS_ULT_CUSTO"

DEFAULT_SQL_SERVER_DRIVER = "ODBC Driver 18 for SQL Server"
DEFAULT_SQL_SERVER_HOST = "rosario.procfit.com.br"
DEFAULT_SQL_SERVER_PORT = "1433"
DEFAULT_SQL_SERVER_DATABASE = "PBS_ROSARIO_DADOS"
DEFAULT_SQL_SERVER_USER = "rosario.ServiceFarma"
DEFAULT_SQL_SERVER_PASSWORD = "gtujku"
DEFAULT_SQL_SERVER_TRUST_CERT = "yes"
DEFAULT_SQL_SERVER_APP = "python.exe"
CONNECTION_KEYS = (
    "driver",
    "host",
    "port",
    "database",
    "user",
    "password",
    "trust_server_certificate",
)


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

        saved = get_sqlserver_connection_settings()

        server = os.getenv("SF_COTADOR_LEGACY_SQLSERVER_HOST", str(saved.get("host", DEFAULT_SQL_SERVER_HOST))).strip()
        if not server:
            raise RuntimeError("SF_COTADOR_LEGACY_SQLSERVER_HOST nao foi informado.")

        port = os.getenv("SF_COTADOR_LEGACY_SQLSERVER_PORT", str(saved.get("port", DEFAULT_SQL_SERVER_PORT))).strip()
        database_name = os.getenv(
            "SF_COTADOR_LEGACY_SQLSERVER_DATABASE",
            str(saved.get("database", DEFAULT_SQL_SERVER_DATABASE)),
        ).strip()
        if not database_name:
            raise RuntimeError("SF_COTADOR_LEGACY_SQLSERVER_DATABASE nao foi informado.")

        driver = os.getenv("SF_COTADOR_LEGACY_SQLSERVER_DRIVER", str(saved.get("driver", DEFAULT_SQL_SERVER_DRIVER))).strip()
        username = os.getenv("SF_COTADOR_LEGACY_SQLSERVER_USER", str(saved.get("user", DEFAULT_SQL_SERVER_USER))).strip()
        password = os.getenv(
            "SF_COTADOR_LEGACY_SQLSERVER_PASSWORD",
            str(saved.get("password", DEFAULT_SQL_SERVER_PASSWORD)),
        ).strip()
        trust_cert = os.getenv(
            "SF_COTADOR_LEGACY_SQLSERVER_TRUST_CERT",
            str(saved.get("trust_server_certificate", DEFAULT_SQL_SERVER_TRUST_CERT)),
        ).strip().lower()
        app_name = os.getenv("SF_COTADOR_LEGACY_SQLSERVER_APP", DEFAULT_SQL_SERVER_APP).strip()

        server_ref = server if not port else f"{server},{port}"
        conn_parts = [
            f"DRIVER={{{driver}}}",
            f"SERVER={server_ref}",
            f"DATABASE={database_name}",
            f"TrustServerCertificate={trust_cert}",
            f"APP={app_name}",
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

    def fetch_ultimos_custos(self) -> list[dict[str, Any]]:
        attempts = [
            f"EXEC {self._qualify_name(LEGACY_QUERY_ULT_CUSTO)}",
            f"SELECT * FROM {self._qualify_name(LEGACY_QUERY_ULT_CUSTO)}",
        ]
        last_error: Exception | None = None
        with self._connect() as conn:
            cur = conn.cursor()
            for statement in attempts:
                try:
                    cur.execute(statement)
                    if cur.description:
                        return self._row_to_dicts(cur)
                except Exception as exc:  # pragma: no cover - fallback path
                    last_error = exc
        if last_error is not None:
            raise last_error
        return []


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
    _ensure_support_tables()


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
                    "VALIDADE PRECO": "",
                }
            )

    resultado.sort(key=lambda row: (str(row["DESCRICAO"]), str(row["Nome"]), str(row["EAN"])))
    return resultado


def _get_local_connection() -> sqlite3.Connection:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _ensure_support_tables() -> None:
    with _get_local_connection() as conn:
        conn.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {TABLE_COTACAO_CAPTADA} (
                Nome TEXT NOT NULL,
                "E-mail/Usuario" TEXT NOT NULL,
                CD_FORNEC INTEGER NOT NULL,
                "Nome Fantasia" TEXT NOT NULL,
                MARCA TEXT NOT NULL,
                CD_PROD INTEGER NOT NULL,
                EAN TEXT NOT NULL,
                DESCRICAO TEXT NOT NULL,
                "VALOR UNITARIO" TEXT NOT NULL,
                "FATOR EMBALAGEM" TEXT NOT NULL,
                "VALIDADE PRECO" TEXT NOT NULL,
                PRIMARY KEY ("E-mail/Usuario", CD_FORNEC, CD_PROD, EAN)
            )
            """
        )
        conn.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {TABLE_CONNECTION_SETTINGS} (
                chave TEXT PRIMARY KEY,
                valor TEXT NOT NULL
            )
            """
        )
        columns = {row["name"] for row in conn.execute(f"PRAGMA table_info({TABLE_CONNECTION_SETTINGS})").fetchall()}
        if columns == {"key", "value"}:
            conn.execute(f"ALTER TABLE {TABLE_CONNECTION_SETTINGS} RENAME TO {TABLE_CONNECTION_SETTINGS}_OLD")
            conn.execute(
                f"""
                CREATE TABLE {TABLE_CONNECTION_SETTINGS} (
                    chave TEXT PRIMARY KEY,
                    valor TEXT NOT NULL
                )
                """
            )
            conn.execute(
                f"""
                INSERT OR REPLACE INTO {TABLE_CONNECTION_SETTINGS} (chave, valor)
                SELECT key, value
                FROM {TABLE_CONNECTION_SETTINGS}_OLD
                """
            )
            conn.execute(f"DROP TABLE {TABLE_CONNECTION_SETTINGS}_OLD")
        conn.commit()


def fetch_cotacoes_captadas() -> list[dict[str, Any]]:
    _ensure_support_tables()
    with _get_local_connection() as conn:
        cur = conn.execute(
            f"""
            SELECT
                Nome,
                "E-mail/Usuario",
                CD_FORNEC,
                "Nome Fantasia",
                MARCA,
                CD_PROD,
                EAN,
                DESCRICAO,
                "VALOR UNITARIO",
                "FATOR EMBALAGEM",
                "VALIDADE PRECO"
            FROM {TABLE_COTACAO_CAPTADA}
            ORDER BY DESCRICAO, Nome, EAN
            """
        )
        return [dict(row) for row in cur.fetchall()]


def upsert_cotacao_captada(row: dict[str, Any]) -> None:
    _ensure_support_tables()
    payload = {
        "Nome": str(row.get("Nome", "")).strip(),
        "E-mail/Usuario": str(row.get("E-mail/Usuario", "")).strip(),
        "CD_FORNEC": int(str(row.get("CD_FORNEC", "0")).strip()),
        "Nome Fantasia": str(row.get("Nome Fantasia", "")).strip(),
        "MARCA": str(row.get("MARCA", "")).strip(),
        "CD_PROD": int(str(row.get("CD_PROD", "0")).strip()),
        "EAN": str(row.get("EAN", "")).strip(),
        "DESCRICAO": str(row.get("DESCRICAO", "")).strip(),
        "VALOR UNITARIO": str(row.get("VALOR UNITARIO", "")).strip(),
        "FATOR EMBALAGEM": str(row.get("FATOR EMBALAGEM", "")).strip(),
        "VALIDADE PRECO": str(row.get("VALIDADE PRECO", "")).strip(),
    }
    with _get_local_connection() as conn:
        conn.execute(
            f"""
            INSERT OR REPLACE INTO {TABLE_COTACAO_CAPTADA} (
                Nome,
                "E-mail/Usuario",
                CD_FORNEC,
                "Nome Fantasia",
                MARCA,
                CD_PROD,
                EAN,
                DESCRICAO,
                "VALOR UNITARIO",
                "FATOR EMBALAGEM",
                "VALIDADE PRECO"
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                payload["Nome"],
                payload["E-mail/Usuario"],
                payload["CD_FORNEC"],
                payload["Nome Fantasia"],
                payload["MARCA"],
                payload["CD_PROD"],
                payload["EAN"],
                payload["DESCRICAO"],
                payload["VALOR UNITARIO"],
                payload["FATOR EMBALAGEM"],
                payload["VALIDADE PRECO"],
            ),
        )
        conn.commit()


def delete_cotacoes_captadas(rows: list[dict[str, Any]]) -> int:
    _ensure_support_tables()
    deleted = 0
    with _get_local_connection() as conn:
        for row in rows:
            cur = conn.execute(
                f"""
                DELETE FROM {TABLE_COTACAO_CAPTADA}
                WHERE "E-mail/Usuario" = ?
                  AND CD_FORNEC = ?
                  AND CD_PROD = ?
                  AND EAN = ?
                """,
                (
                    str(row.get("E-mail/Usuario", "")),
                    int(str(row.get("CD_FORNEC", "0"))),
                    int(str(row.get("CD_PROD", "0"))),
                    str(row.get("EAN", "")),
                ),
            )
            deleted += cur.rowcount
        conn.commit()
    return deleted


def _normalize_sqlserver_driver_name(value: str) -> str:
    return " ".join(value.strip().casefold().split())


def _extract_sqlserver_odbc_major_version(driver_name: str) -> int | None:
    normalized = _normalize_sqlserver_driver_name(driver_name)
    marker = "odbc driver "
    if not normalized.startswith(marker) or " for sql server" not in normalized:
        return None
    digits: list[str] = []
    for char in normalized[len(marker) :]:
        if char.isdigit():
            digits.append(char)
        else:
            break
    return int("".join(digits)) if digits else None


def resolve_sqlserver_driver(preferred_driver: str, installed_drivers: list[str]) -> str | None:
    preferred = preferred_driver.strip()
    installed = [item.strip() for item in installed_drivers if item.strip()]
    if not installed:
        return preferred or None

    by_normalized = {_normalize_sqlserver_driver_name(item): item for item in installed}
    if preferred:
        exact = by_normalized.get(_normalize_sqlserver_driver_name(preferred))
        if exact:
            return exact

    sql_server_odbc = [item for item in installed if "sql server" in _normalize_sqlserver_driver_name(item)]
    versioned = [
        (item, _extract_sqlserver_odbc_major_version(item))
        for item in sql_server_odbc
    ]
    versioned = [(item, version) for item, version in versioned if version is not None]
    if versioned:
        versioned.sort(key=lambda pair: pair[1], reverse=True)
        return versioned[0][0]

    for fallback in ("SQL Server Native Client 11.0", "SQL Server"):
        match = by_normalized.get(_normalize_sqlserver_driver_name(fallback))
        if match:
            return match

    return sql_server_odbc[0] if sql_server_odbc else None


def get_sqlserver_connection_settings() -> dict[str, str]:
    _ensure_support_tables()
    defaults = {
        "driver": DEFAULT_SQL_SERVER_DRIVER,
        "host": DEFAULT_SQL_SERVER_HOST,
        "port": DEFAULT_SQL_SERVER_PORT,
        "database": DEFAULT_SQL_SERVER_DATABASE,
        "user": DEFAULT_SQL_SERVER_USER,
        "password": DEFAULT_SQL_SERVER_PASSWORD,
        "trust_server_certificate": DEFAULT_SQL_SERVER_TRUST_CERT,
    }
    with _get_local_connection() as conn:
        cur = conn.execute(f"SELECT chave, valor FROM {TABLE_CONNECTION_SETTINGS}")
        for row in cur.fetchall():
            key = str(row["chave"])
            if key in defaults:
                defaults[key] = str(row["valor"])
    return defaults


def save_sqlserver_connection_settings(payload: dict[str, str]) -> None:
    _ensure_support_tables()
    with _get_local_connection() as conn:
        for key in CONNECTION_KEYS:
            conn.execute(
                f"""
                INSERT INTO {TABLE_CONNECTION_SETTINGS} (chave, valor)
                VALUES (?, ?)
                ON CONFLICT(chave) DO UPDATE SET valor=excluded.valor
                """,
                (key, str(payload.get(key, "")).strip()),
            )
        conn.commit()


def reset_legacy_adapter() -> None:
    global _LEGACY_ADAPTER
    _LEGACY_ADAPTER = None


def get_sqlserver_runtime_diagnostics(host: str = "", port: str = "") -> dict[str, Any]:
    diagnostics: dict[str, Any] = {
        "python_executable": DEFAULT_SQL_SERVER_APP,
        "data_dir": str(DATA_DIR),
        "db_path": str(DB_PATH),
        "data_dir_writable": os.access(DATA_DIR, os.W_OK) if DATA_DIR.exists() else os.access(DATA_DIR.parent, os.W_OK),
        "frozen": False,
        "host": host,
        "port": port,
        "pyodbc_installed": False,
        "odbc_drivers": [],
    }
    try:
        import pyodbc

        diagnostics["pyodbc_installed"] = True
        diagnostics["odbc_drivers"] = list(pyodbc.drivers())
    except Exception as exc:  # pragma: no cover - diagnostic path
        diagnostics["pyodbc_error"] = str(exc)

    host_clean = str(host).strip()
    port_clean = str(port).strip()
    if host_clean and port_clean.isdigit():
        try:
            with socket.create_connection((host_clean, int(port_clean)), timeout=3):
                diagnostics["host_port_reachable"] = True
        except Exception as exc:  # pragma: no cover - network dependent
            diagnostics["host_port_reachable"] = False
            diagnostics["host_port_error"] = str(exc)

    return diagnostics


def _as_float(value: Any) -> float | None:
    raw = str(value).strip().replace(".", "").replace(",", ".")
    if not raw:
        return None
    try:
        return float(raw)
    except ValueError:
        return None


def _find_first(row: dict[str, Any], *keys: str) -> Any:
    lowered = {str(key).casefold(): value for key, value in row.items()}
    for key in keys:
        if key.casefold() in lowered:
            return lowered[key.casefold()]
    return None


def fetch_cs_ult_custo() -> list[dict[str, Any]]:
    return _get_legacy_adapter().fetch_ultimos_custos()


def fetch_cs_compara_01() -> list[dict[str, Any]]:
    capturas = fetch_cotacoes_captadas()
    try:
        ultimos_custos = fetch_cs_ult_custo()
    except Exception:
        ultimos_custos = []

    custos_por_chave: dict[tuple[str, str], dict[str, Any]] = {}
    for row in ultimos_custos:
        ean = str(_find_first(row, "EAN", "cod_barra", "codigo_barras") or "").strip()
        cd_prod = str(_find_first(row, "CD_PROD", "cod_produto", "produto") or "").strip()
        if ean:
            custos_por_chave[("ean", ean)] = row
        if cd_prod:
            custos_por_chave[("prod", cd_prod)] = row

    resultado: list[dict[str, Any]] = []
    for row in capturas:
        cost_row = custos_por_chave.get(("ean", str(row.get("EAN", "")).strip())) or custos_por_chave.get(
            ("prod", str(row.get("CD_PROD", "")).strip())
        )
        ultimo_custo = _as_float(_find_first(cost_row or {}, "ultimo_custo", "ult_custo", "custo", "valor"))
        valor_cotado = _as_float(row.get("VALOR UNITARIO"))
        validade_preco = str(row.get("VALIDADE PRECO", "")).strip()
        compara = "Sem custo"
        div_custo = ""
        if ultimo_custo is not None and valor_cotado is not None:
            if valor_cotado > ultimo_custo:
                compara = "Acima"
            elif valor_cotado < ultimo_custo:
                compara = "Abaixo"
            else:
                compara = "Igual"
            if ultimo_custo:
                div_custo = f"{((valor_cotado - ultimo_custo) / ultimo_custo) * 100:.2f}%"

        resultado.append(
            {
                "CD_PROD": row.get("CD_PROD", ""),
                "EAN": row.get("EAN", ""),
                "DESCRICAO": row.get("DESCRICAO", ""),
                "VALOR UNITARIO": row.get("VALOR UNITARIO", ""),
                "FATOR EMBALAGEM": row.get("FATOR EMBALAGEM", ""),
                "VALIDADE PRECO": validade_preco,
                "ultimo_custo": "" if ultimo_custo is None else f"{ultimo_custo:.4f}",
                "valida_data": "OK" if validade_preco else "Sem validade",
                "valor_cotado": "" if valor_cotado is None else f"{valor_cotado:.4f}",
                "compara_ult_custo": compara,
                "div_custo": div_custo,
                "ult_entrada_data": str(_find_first(cost_row or {}, "ult_entrada_data", "data", "data_entrada") or ""),
                "cod_produto": str(_find_first(cost_row or {}, "cod_produto", "CD_PROD", "produto") or row.get("CD_PROD", "")),
                "Nome": row.get("Nome", ""),
                "E-mail/Usuario": row.get("E-mail/Usuario", ""),
                "CD_FORNEC": row.get("CD_FORNEC", ""),
                "Nome Fantasia": row.get("Nome Fantasia", ""),
                "MARCA": row.get("MARCA", ""),
            }
        )

    return resultado


def fetch_cs_compara_fornec() -> dict[str, Any]:
    rows = fetch_cs_compara_01()
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        grouped.setdefault(str(row.get("CD_PROD", "")), []).append(row)

    result_rows: list[dict[str, Any]] = []
    for cd_prod, items in grouped.items():
        valid_items = [item for item in items if _as_float(item.get("valor_cotado")) is not None]
        if not valid_items:
            continue
        menor = min(valid_items, key=lambda item: _as_float(item.get("valor_cotado")) or 0.0)
        menor_valor = _as_float(menor.get("valor_cotado")) or 0.0
        ultimo_custo = _as_float(menor.get("ultimo_custo")) or 0.0
        var_preco = f"{((menor_valor - ultimo_custo) / ultimo_custo) * 100:.2f}%" if ultimo_custo else ""
        result_rows.append(
            {
                "CD_PROD": cd_prod,
                "DESCRICAO": menor.get("DESCRICAO", ""),
                "ultimo_custo": menor.get("ultimo_custo", ""),
                "menor_valor": f"{menor_valor:.4f}",
                "var_preco": var_preco,
                "CD_FORNEC": menor.get("CD_FORNEC", ""),
                "Fornecedor": menor.get("Nome Fantasia", ""),
                "Nome": menor.get("Nome", ""),
                "Contato": menor.get("E-mail/Usuario", ""),
            }
        )

    result_rows.sort(key=lambda row: (str(row["DESCRICAO"]), str(row["Fornecedor"])))
    return {
        "query_name": "CS_COMPARA_FORNEC",
        "columns": (
            "CD_PROD",
            "DESCRICAO",
            "ultimo_custo",
            "menor_valor",
            "var_preco",
            "CD_FORNEC",
            "Fornecedor",
            "Nome",
            "Contato",
        ),
        "rows": result_rows,
    }
