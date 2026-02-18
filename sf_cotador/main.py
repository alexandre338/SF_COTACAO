import tkinter as tk
from tkinter import messagebox, ttk

import database

WINDOW_WIDTH = 900
WINDOW_HEIGHT = 420

BG_APP = "#111827"
BG_SURFACE = "#1f2937"
BG_SURFACE_HOVER = "#273548"
TEXT_PRIMARY = "#f3f4f6"
TEXT_SECONDARY = "#9ca3af"
ACCENT = "#22d3ee"


def style_hover_button(button: tk.Button, normal_bg: str, hover_bg: str) -> None:
    button.bind("<Enter>", lambda _: button.config(bg=hover_bg))
    button.bind("<Leave>", lambda _: button.config(bg=normal_bg))


def style_hover_frame(frame: tk.Frame, normal_bg: str, hover_bg: str) -> None:
    frame.bind("<Enter>", lambda _: frame.config(bg=hover_bg))
    frame.bind("<Leave>", lambda _: frame.config(bg=normal_bg))


def clear_frame(frame: tk.Frame) -> None:
    for widget in frame.winfo_children():
        widget.destroy()


def is_valid_email(email: str) -> bool:
    email = email.strip()
    return "@" in email and "." in email.split("@")[-1]


def create_modal(parent: tk.Tk, title: str) -> tuple[tk.Toplevel, tk.Frame, tk.Frame]:
    modal = tk.Toplevel(parent)
    modal.title(title)
    modal.geometry("980x600")
    modal.minsize(980, 600)
    modal.transient(parent)
    modal.grab_set()
    modal.configure(bg=BG_APP)

    body = tk.Frame(modal, bg=BG_APP, padx=14, pady=14)
    body.pack(fill="both", expand=True)
    body.grid_rowconfigure(1, weight=1)
    body.grid_columnconfigure(0, weight=1)

    content = tk.Frame(body, bg=BG_SURFACE, highlightthickness=1, highlightbackground="#374151", padx=12, pady=12)
    content.grid(row=1, column=0, sticky="nsew", pady=(4, 0))
    content.grid_rowconfigure(2, weight=1)
    content.grid_columnconfigure(0, weight=1)
    return modal, body, content


def create_add_button(parent: tk.Widget, on_add: callable) -> None:
    bar = tk.Frame(parent, bg=BG_SURFACE)
    bar.grid(row=1, column=0, sticky="e", pady=(0, 10))

    btn_add = tk.Button(
        bar,
        text="Adicionar registro",
        command=on_add,
        bg="#1f3b2d",
        fg=TEXT_PRIMARY,
        activebackground="#2f5f45",
        activeforeground=TEXT_PRIMARY,
        relief="flat",
        bd=0,
        cursor="hand2",
        padx=14,
        pady=8,
        font=("Segoe UI", 10, "bold"),
    )
    btn_add.pack(side="left")
    style_hover_button(btn_add, "#1f3b2d", "#2f5f45")


def create_action_buttons(parent: tk.Widget, on_save: callable, on_close: callable) -> None:
    buttons = tk.Frame(parent, bg=BG_APP)
    buttons.grid(row=2, column=0, sticky="ew", pady=(10, 0))
    buttons.grid_columnconfigure(0, weight=1)

    main_row = tk.Frame(buttons, bg=BG_APP)
    main_row.grid(row=0, column=0, sticky="e")

    btn_save = tk.Button(
        main_row,
        text="Salvar",
        command=on_save,
        bg="#0f172a",
        fg=TEXT_PRIMARY,
        activebackground=ACCENT,
        activeforeground="#0b1220",
        relief="flat",
        bd=0,
        cursor="hand2",
        padx=14,
        pady=8,
        font=("Segoe UI", 10, "bold"),
    )
    btn_save.pack(side="left", padx=(0, 8))
    style_hover_button(btn_save, "#0f172a", "#1e293b")

    btn_close = tk.Button(
        main_row,
        text="Fechar",
        command=on_close,
        bg="#334155",
        fg=TEXT_PRIMARY,
        activebackground="#475569",
        activeforeground=TEXT_PRIMARY,
        relief="flat",
        bd=0,
        cursor="hand2",
        padx=14,
        pady=8,
        font=("Segoe UI", 10, "bold"),
    )
    btn_close.pack(side="left")
    style_hover_button(btn_close, "#334155", "#475569")


def create_navigation_bar(parent: tk.Widget, tree: ttk.Treeview, on_select_row: callable) -> tuple[tk.Label, callable]:
    nav = tk.Frame(parent, bg=BG_SURFACE)
    nav.grid(row=3, column=0, sticky="ew", pady=(8, 0))
    nav.grid_columnconfigure(6, weight=1)

    count_label = tk.Label(
        nav,
        text="Registros: 0",
        bg=BG_SURFACE,
        fg=TEXT_SECONDARY,
        font=("Segoe UI", 9, "bold"),
    )
    count_label.grid(row=0, column=0, sticky="w")

    def select_at(index: int) -> None:
        items = tree.get_children()
        if not items:
            return
        idx = max(0, min(index, len(items) - 1))
        item_id = items[idx]
        tree.selection_set(item_id)
        tree.focus(item_id)
        tree.see(item_id)
        on_select_row(tree.item(item_id, "values"))

    def current_index() -> int:
        items = tree.get_children()
        if not items:
            return -1
        sel = tree.selection()
        if not sel:
            return 0
        return items.index(sel[0])

    def first_item() -> None:
        select_at(0)

    def prev_item() -> None:
        select_at(current_index() - 1)

    def next_item() -> None:
        select_at(current_index() + 1)

    def last_item() -> None:
        items = tree.get_children()
        select_at(len(items) - 1)

    btn_first = tk.Button(nav, text="|<", command=first_item, bg="#0f172a", fg=TEXT_PRIMARY, relief="flat", bd=0, width=4)
    btn_prev = tk.Button(nav, text="<", command=prev_item, bg="#0f172a", fg=TEXT_PRIMARY, relief="flat", bd=0, width=4)
    btn_next = tk.Button(nav, text=">", command=next_item, bg="#0f172a", fg=TEXT_PRIMARY, relief="flat", bd=0, width=4)
    btn_last = tk.Button(nav, text=">|", command=last_item, bg="#0f172a", fg=TEXT_PRIMARY, relief="flat", bd=0, width=4)

    btn_first.grid(row=0, column=2, padx=(8, 4))
    btn_prev.grid(row=0, column=3, padx=4)
    btn_next.grid(row=0, column=4, padx=4)
    btn_last.grid(row=0, column=5, padx=4)

    for btn in (btn_first, btn_prev, btn_next, btn_last):
        style_hover_button(btn, "#0f172a", "#1e293b")

    def sync_counter() -> None:
        total = len(tree.get_children())
        count_label.config(text=f"Registros: {total}")

    tree.bind("<<TreeviewSelect>>", lambda _: on_select_row(tree.item(tree.selection()[0], "values")) if tree.selection() else None)
    return count_label, sync_counter


def show_fornecedores_modal(parent: tk.Tk) -> None:
    modal, body, content = create_modal(parent, "Cadastro de Fornecedores")

    form = tk.Frame(content, bg=BG_SURFACE)
    form.grid(row=0, column=0, sticky="ew", pady=(0, 10))
    form.grid_columnconfigure(1, weight=1)
    form.grid_columnconfigure(3, weight=1)

    id_var = tk.StringVar()
    procfit_var = tk.StringVar()
    nome_var = tk.StringVar()
    nome_fantasia_var = tk.StringVar()

    for label, var, row, col in (
        ("ID", id_var, 0, 0),
        ("Procfit", procfit_var, 0, 2),
        ("Nome", nome_var, 1, 0),
        ("Nome Fantasia", nome_fantasia_var, 1, 2),
    ):
        tk.Label(form, text=label, bg=BG_SURFACE, fg=TEXT_PRIMARY, font=("Segoe UI", 10, "bold")).grid(
            row=row, column=col, sticky="w", padx=(0, 8), pady=4
        )
        tk.Entry(
            form,
            textvariable=var,
            bg="#0f172a",
            fg=TEXT_PRIMARY,
            insertbackground=TEXT_PRIMARY,
            relief="flat",
            font=("Segoe UI", 10),
        ).grid(row=row, column=col + 1, sticky="ew", padx=(0, 12), pady=4, ipady=4)

    list_frame = tk.Frame(content, bg=BG_SURFACE)
    list_frame.grid(row=2, column=0, sticky="nsew")
    list_frame.grid_rowconfigure(0, weight=1)
    list_frame.grid_columnconfigure(0, weight=1)

    columns = ("ID", "Procfit", "Nome", "Nome Fantasia")
    tree = ttk.Treeview(list_frame, columns=columns, show="headings")
    tree.grid(row=0, column=0, sticky="nsew")
    scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=tree.yview)
    scrollbar.grid(row=0, column=1, sticky="ns")
    tree.configure(yscrollcommand=scrollbar.set)

    tree.heading("ID", text="ID")
    tree.heading("Procfit", text="Procfit")
    tree.heading("Nome", text="Nome")
    tree.heading("Nome Fantasia", text="Nome Fantasia")
    tree.column("ID", width=70, anchor="center")
    tree.column("Procfit", width=120, anchor="center")
    tree.column("Nome", width=360, anchor="w")
    tree.column("Nome Fantasia", width=220, anchor="w")

    def on_select_row(values: tuple[str, ...]) -> None:
        id_var.set(str(values[0]))
        procfit_var.set(str(values[1]))
        nome_var.set(str(values[2]))
        nome_fantasia_var.set(str(values[3]))

    _, sync_counter = create_navigation_bar(content, tree, on_select_row)

    def refresh_tree() -> None:
        for item in tree.get_children():
            tree.delete(item)
        for row in database.fetch_fornecedores():
            tree.insert("", "end", values=(row["ID"], row["Procfit"], row["Nome"], row["Nome Fantasia"]))
        sync_counter()
        items = tree.get_children()
        if items:
            first = items[0]
            tree.selection_set(first)
            tree.focus(first)
            tree.see(first)
            on_select_row(tree.item(first, "values"))

    def salvar() -> None:
        try:
            id_fornec = int(id_var.get().strip())
            procfit = int(procfit_var.get().strip())
        except ValueError:
            messagebox.showerror("Dados invalidos", "ID e Procfit devem ser numeros inteiros.", parent=modal)
            return
        nome = nome_var.get().strip()
        nome_fantasia = nome_fantasia_var.get().strip()
        if not nome or not nome_fantasia:
            messagebox.showerror("Dados invalidos", "Preencha Nome e Nome Fantasia.", parent=modal)
            return
        try:
            database.insert_fornecedor(id_fornec, procfit, nome, nome_fantasia)
        except Exception as exc:
            messagebox.showerror("Erro ao salvar", str(exc), parent=modal)
            return
        id_var.set("")
        procfit_var.set("")
        nome_var.set("")
        nome_fantasia_var.set("")
        refresh_tree()

    def adicionar_registro() -> None:
        id_var.set("")
        procfit_var.set("")
        nome_var.set("")
        nome_fantasia_var.set("")

    create_add_button(content, adicionar_registro)
    create_action_buttons(body, salvar, modal.destroy)
    refresh_tree()
    modal.wait_window()


def show_representantes_modal(parent: tk.Tk) -> None:
    modal, body, content = create_modal(parent, "Cadastro de Representantes")

    form = tk.Frame(content, bg=BG_SURFACE)
    form.grid(row=0, column=0, sticky="ew", pady=(0, 10))
    for idx in (1, 3, 5):
        form.grid_columnconfigure(idx, weight=1)

    vars_map = {
        "CodRepres": tk.StringVar(),
        "Nome": tk.StringVar(),
        "Login": tk.StringVar(),
        "Cod Forn": tk.StringVar(),
        "Fornecedor": tk.StringVar(),
        "Cod Marca": tk.StringVar(),
        "Marca": tk.StringVar(),
    }

    fields = (
        ("CodRepres", 0, 0),
        ("Nome", 0, 2),
        ("Login", 0, 4),
        ("Cod Forn", 1, 0),
        ("Fornecedor", 1, 2),
        ("Cod Marca", 1, 4),
        ("Marca", 2, 0),
    )

    for label, row, col in fields:
        tk.Label(form, text=label, bg=BG_SURFACE, fg=TEXT_PRIMARY, font=("Segoe UI", 10, "bold")).grid(
            row=row, column=col, sticky="w", padx=(0, 8), pady=4
        )
        tk.Entry(
            form,
            textvariable=vars_map[label],
            bg="#0f172a",
            fg=TEXT_PRIMARY,
            insertbackground=TEXT_PRIMARY,
            relief="flat",
            font=("Segoe UI", 10),
        ).grid(row=row, column=col + 1, sticky="ew", padx=(0, 12), pady=4, ipady=4)

    list_frame = tk.Frame(content, bg=BG_SURFACE)
    list_frame.grid(row=2, column=0, sticky="nsew")
    list_frame.grid_rowconfigure(0, weight=1)
    list_frame.grid_columnconfigure(0, weight=1)

    columns = ("CodRepres", "Nome", "Login", "Cod Forn", "Fornecedor", "Cod Marca", "Marca")
    tree = ttk.Treeview(list_frame, columns=columns, show="headings")
    tree.grid(row=0, column=0, sticky="nsew")
    scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=tree.yview)
    scrollbar.grid(row=0, column=1, sticky="ns")
    tree.configure(yscrollcommand=scrollbar.set)

    for col in columns:
        tree.heading(col, text=col)
    tree.column("CodRepres", width=100, anchor="center")
    tree.column("Nome", width=200, anchor="w")
    tree.column("Login", width=220, anchor="w")
    tree.column("Cod Forn", width=100, anchor="center")
    tree.column("Fornecedor", width=220, anchor="w")
    tree.column("Cod Marca", width=100, anchor="center")
    tree.column("Marca", width=160, anchor="w")

    def on_select_row(values: tuple[str, ...]) -> None:
        vars_map["CodRepres"].set(str(values[0]))
        vars_map["Nome"].set(str(values[1]))
        vars_map["Login"].set(str(values[2]))
        vars_map["Cod Forn"].set(str(values[3]))
        vars_map["Fornecedor"].set(str(values[4]))
        vars_map["Cod Marca"].set(str(values[5]))
        vars_map["Marca"].set(str(values[6]))

    _, sync_counter = create_navigation_bar(content, tree, on_select_row)

    def refresh_tree() -> None:
        for item in tree.get_children():
            tree.delete(item)
        for row in database.fetch_representantes():
            tree.insert(
                "",
                "end",
                values=(
                    row["CodRepres"],
                    row["Nome"],
                    row["Login"],
                    row["Cod Forn"],
                    row["Fornecedor"],
                    row["Cod Marca"],
                    row["Marca"],
                ),
            )
        sync_counter()
        items = tree.get_children()
        if items:
            first = items[0]
            tree.selection_set(first)
            tree.focus(first)
            tree.see(first)
            on_select_row(tree.item(first, "values"))

    def salvar() -> None:
        try:
            cod_repres = int(vars_map["CodRepres"].get().strip())
            cod_forn = int(vars_map["Cod Forn"].get().strip())
            cod_marca = int(vars_map["Cod Marca"].get().strip())
        except ValueError:
            messagebox.showerror("Dados invalidos", "CodRepres, Cod Forn e Cod Marca devem ser numeros inteiros.", parent=modal)
            return

        nome = vars_map["Nome"].get().strip()
        login = vars_map["Login"].get().strip()
        fornecedor = vars_map["Fornecedor"].get().strip()
        marca = vars_map["Marca"].get().strip()
        if not nome or not login or not fornecedor or not marca:
            messagebox.showerror("Dados invalidos", "Preencha todos os campos de texto.", parent=modal)
            return
        if not is_valid_email(login):
            messagebox.showerror("Dados invalidos", "Login deve estar no formato de e-mail.", parent=modal)
            return

        try:
            database.insert_representante(cod_repres, nome, login, cod_forn, fornecedor, cod_marca, marca)
        except Exception as exc:
            messagebox.showerror("Erro ao salvar", str(exc), parent=modal)
            return

        for var in vars_map.values():
            var.set("")
        refresh_tree()

    def adicionar_registro() -> None:
        for var in vars_map.values():
            var.set("")

    create_add_button(content, adicionar_registro)
    create_action_buttons(body, salvar, modal.destroy)
    refresh_tree()
    modal.wait_window()


def show_contatos_modal(parent: tk.Tk) -> None:
    modal, body, content = create_modal(parent, "Cadastro de Contatos")

    form = tk.Frame(content, bg=BG_SURFACE)
    form.grid(row=0, column=0, sticky="ew", pady=(0, 10))
    form.grid_columnconfigure(1, weight=1)
    form.grid_columnconfigure(3, weight=1)

    d_var = tk.StringVar()
    nome_var = tk.StringVar()
    email_var = tk.StringVar()
    situacao_var = tk.StringVar(value="Ativo")
    acoes_var = tk.StringVar()

    entries = (
        ("D", d_var, 0, 0),
        ("Nome", nome_var, 0, 2),
        ("E-mail/Usuario", email_var, 1, 0),
        ("Acoes", acoes_var, 1, 2),
    )

    for label, var, row, col in entries:
        tk.Label(form, text=label, bg=BG_SURFACE, fg=TEXT_PRIMARY, font=("Segoe UI", 10, "bold")).grid(
            row=row, column=col, sticky="w", padx=(0, 8), pady=4
        )
        tk.Entry(
            form,
            textvariable=var,
            bg="#0f172a",
            fg=TEXT_PRIMARY,
            insertbackground=TEXT_PRIMARY,
            relief="flat",
            font=("Segoe UI", 10),
        ).grid(row=row, column=col + 1, sticky="ew", padx=(0, 12), pady=4, ipady=4)

    tk.Label(form, text="Situacao", bg=BG_SURFACE, fg=TEXT_PRIMARY, font=("Segoe UI", 10, "bold")).grid(
        row=2, column=0, sticky="w", padx=(0, 8), pady=4
    )
    cmb_situacao = ttk.Combobox(form, textvariable=situacao_var, values=("Ativo", "Inativo"), state="readonly")
    cmb_situacao.grid(row=2, column=1, sticky="ew", padx=(0, 12), pady=4, ipady=2)

    list_frame = tk.Frame(content, bg=BG_SURFACE)
    list_frame.grid(row=2, column=0, sticky="nsew")
    list_frame.grid_rowconfigure(0, weight=1)
    list_frame.grid_columnconfigure(0, weight=1)

    columns = ("D", "Nome", "E-mail/Usuario", "Situacao", "Acoes")
    tree = ttk.Treeview(list_frame, columns=columns, show="headings")
    tree.grid(row=0, column=0, sticky="nsew")
    scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=tree.yview)
    scrollbar.grid(row=0, column=1, sticky="ns")
    tree.configure(yscrollcommand=scrollbar.set)

    for col in columns:
        tree.heading(col, text=col)
    tree.column("D", width=70, anchor="center")
    tree.column("Nome", width=180, anchor="w")
    tree.column("E-mail/Usuario", width=240, anchor="w")
    tree.column("Situacao", width=100, anchor="center")
    tree.column("Acoes", width=220, anchor="w")

    def on_select_row(values: tuple[str, ...]) -> None:
        d_var.set(str(values[0]))
        nome_var.set(str(values[1]))
        email_var.set(str(values[2]))
        situacao_var.set(str(values[3]))
        acoes_var.set(str(values[4]))

    _, sync_counter = create_navigation_bar(content, tree, on_select_row)

    def refresh_tree() -> None:
        for item in tree.get_children():
            tree.delete(item)
        for row in database.fetch_contatos():
            tree.insert(
                "",
                "end",
                values=(row["D"], row["Nome"], row["E-mail/Usuario"], row["Situacao"], row["Acoes"]),
            )
        sync_counter()
        items = tree.get_children()
        if items:
            first = items[0]
            tree.selection_set(first)
            tree.focus(first)
            tree.see(first)
            on_select_row(tree.item(first, "values"))

    def salvar() -> None:
        try:
            d_contato = int(d_var.get().strip())
        except ValueError:
            messagebox.showerror("Dados invalidos", "D deve ser numero inteiro.", parent=modal)
            return

        nome = nome_var.get().strip()
        email = email_var.get().strip()
        situacao = situacao_var.get().strip()
        acoes = acoes_var.get().strip()
        if not nome or not email or not acoes:
            messagebox.showerror("Dados invalidos", "Preencha Nome, E-mail/Usuario e Acoes.", parent=modal)
            return
        if not is_valid_email(email):
            messagebox.showerror("Dados invalidos", "E-mail/Usuario deve estar no formato de e-mail.", parent=modal)
            return
        if situacao not in ("Ativo", "Inativo"):
            messagebox.showerror("Dados invalidos", "Situacao deve ser Ativo ou Inativo.", parent=modal)
            return

        try:
            database.insert_contato(d_contato, nome, email, situacao, acoes)
        except Exception as exc:
            messagebox.showerror("Erro ao salvar", str(exc), parent=modal)
            return

        d_var.set("")
        nome_var.set("")
        email_var.set("")
        situacao_var.set("Ativo")
        acoes_var.set("")
        refresh_tree()

    def adicionar_registro() -> None:
        d_var.set("")
        nome_var.set("")
        email_var.set("")
        situacao_var.set("Ativo")
        acoes_var.set("")

    create_add_button(content, adicionar_registro)
    create_action_buttons(body, salvar, modal.destroy)
    refresh_tree()
    modal.wait_window()


def main() -> None:
    database.init_db()

    root = tk.Tk()
    root.title("SF COTADOR")
    root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
    root.minsize(WINDOW_WIDTH, WINDOW_HEIGHT)
    root.configure(bg=BG_APP)

    base = tk.Frame(root, bg=BG_APP, padx=14, pady=14)
    base.pack(fill="both", expand=True)
    base.grid_rowconfigure(0, weight=15)
    base.grid_rowconfigure(1, weight=75)
    base.grid_rowconfigure(2, weight=5)
    base.grid_columnconfigure(0, weight=1)

    header_row = tk.Frame(base, bg=BG_SURFACE, highlightthickness=1, highlightbackground="#374151")
    header_row.grid(row=0, column=0, sticky="nsew", pady=(0, 10))
    header_row.grid_columnconfigure(0, weight=1)
    tk.Label(
        header_row,
        text="Sistema de Cotacao",
        bg=BG_SURFACE,
        fg=TEXT_PRIMARY,
        anchor="center",
        padx=14,
        font=("Segoe UI", 12, "bold"),
    ).grid(row=0, column=0, sticky="nsew")

    content_row = tk.Frame(base, bg=BG_APP)
    content_row.grid(row=1, column=0, sticky="nsew")
    content_row.grid_columnconfigure(0, weight=1)
    content_row.grid_columnconfigure(1, weight=4)
    content_row.grid_rowconfigure(0, weight=1)

    cadastros_col = tk.Frame(content_row, bg=BG_SURFACE, padx=12, pady=12, highlightthickness=1, highlightbackground="#374151")
    cadastros_col.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
    tk.Label(
        cadastros_col,
        text="Cadastros",
        bg=BG_SURFACE,
        fg=ACCENT,
        anchor="w",
        font=("Segoe UI", 11, "bold"),
    ).pack(fill="x", pady=(0, 10))

    acoes_col = tk.Frame(content_row, bg=BG_SURFACE, padx=14, pady=12, highlightthickness=1, highlightbackground="#374151")
    acoes_col.grid(row=0, column=1, sticky="nsew")
    acoes_col.grid_columnconfigure(0, weight=1)
    acoes_col.grid_rowconfigure(1, weight=1)

    title_label = tk.Label(
        acoes_col,
        text="Acoes",
        bg=BG_SURFACE,
        fg=ACCENT,
        anchor="w",
        font=("Segoe UI", 11, "bold"),
    )
    title_label.grid(row=0, column=0, sticky="w")

    actions_body = tk.Frame(acoes_col, bg=BG_SURFACE)
    actions_body.grid(row=1, column=0, sticky="nsew", pady=(10, 0))
    actions_body.grid_columnconfigure(0, weight=1)
    actions_body.grid_rowconfigure(0, weight=1)

    def show_actions_reserved() -> None:
        title_label.config(text="Acoes")
        clear_frame(actions_body)
        card = tk.Frame(actions_body, bg="#172033", highlightthickness=1, highlightbackground="#334155")
        card.grid(row=0, column=0, sticky="nsew")
        style_hover_frame(card, "#172033", BG_SURFACE_HOVER)
        tk.Label(
            card,
            text="Espaco reservado para o futuro conjunto de acoes.",
            bg="#172033",
            fg=TEXT_SECONDARY,
            padx=12,
            pady=12,
            anchor="nw",
            justify="left",
            font=("Segoe UI", 10),
        ).pack(fill="both", expand=True)

    for text, cmd in (
        ("Fornecedores", lambda: show_fornecedores_modal(root)),
        ("Representantes", lambda: show_representantes_modal(root)),
        ("Contatos", lambda: show_contatos_modal(root)),
    ):
        btn = tk.Button(
            cadastros_col,
            text=text,
            bg="#0f172a",
            fg=TEXT_PRIMARY,
            activebackground=ACCENT,
            activeforeground="#0b1220",
            relief="flat",
            bd=0,
            cursor="hand2",
            padx=8,
            pady=8,
            font=("Segoe UI", 10, "bold"),
            command=cmd,
        )
        btn.pack(fill="x", pady=4)
        style_hover_button(btn, "#0f172a", "#1e293b")

    show_actions_reserved()

    footer_row = tk.Frame(base, bg=BG_APP)
    footer_row.grid(row=2, column=0, sticky="nsew")
    footer_row.grid_columnconfigure(0, weight=1)
    footer_row.grid_rowconfigure(0, weight=1)
    tk.Label(
        footer_row,
        text="- by Service Farma",
        bg=BG_APP,
        fg=TEXT_SECONDARY,
        font=("Segoe UI", 9, "italic"),
    ).grid(row=0, column=0, sticky="se")

    root.mainloop()


if __name__ == "__main__":
    main()
