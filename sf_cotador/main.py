import tkinter as tk
from tkinter import filedialog, messagebox, ttk

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


def create_tree_with_scrollbars(
    parent: tk.Widget,
    columns: tuple[str, ...],
) -> tuple[ttk.Treeview, ttk.Scrollbar, ttk.Scrollbar]:
    tree = ttk.Treeview(parent, columns=columns, show="headings")
    tree.grid(row=0, column=0, sticky="nsew")

    scrollbar_y = ttk.Scrollbar(parent, orient="vertical", command=tree.yview)
    scrollbar_y.grid(row=0, column=1, sticky="ns")

    scrollbar_x = ttk.Scrollbar(parent, orient="horizontal", command=tree.xview)
    scrollbar_x.grid(row=1, column=0, sticky="ew")

    tree.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)
    return tree, scrollbar_y, scrollbar_x


def is_valid_email(email: str) -> bool:
    email = email.strip()
    return "@" in email and "." in email.split("@")[-1]


def summarize_selected_values(selected_values: set[str]) -> str:
    if not selected_values:
        return "Todos"
    if len(selected_values) == 1:
        return next(iter(selected_values))
    return f"{len(selected_values)} selecionados"


def open_multi_select_dialog(
    parent: tk.Toplevel,
    title: str,
    options: list[str],
    selected_values: set[str],
    on_apply: callable,
) -> None:
    dialog = tk.Toplevel(parent)
    dialog.title(title)
    dialog.geometry("420x420")
    dialog.minsize(420, 420)
    dialog.transient(parent)
    dialog.grab_set()
    dialog.configure(bg=BG_APP)

    body = tk.Frame(dialog, bg=BG_APP, padx=12, pady=12)
    body.pack(fill="both", expand=True)
    body.grid_rowconfigure(1, weight=1)
    body.grid_columnconfigure(0, weight=1)

    tk.Label(
        body,
        text=title,
        bg=BG_APP,
        fg=TEXT_PRIMARY,
        font=("Segoe UI", 11, "bold"),
    ).grid(row=0, column=0, sticky="w", pady=(0, 10))

    list_frame = tk.Frame(body, bg=BG_SURFACE)
    list_frame.grid(row=1, column=0, sticky="nsew")
    list_frame.grid_rowconfigure(0, weight=1)
    list_frame.grid_columnconfigure(0, weight=1)

    listbox = tk.Listbox(
        list_frame,
        selectmode="multiple",
        bg="#0f172a",
        fg=TEXT_PRIMARY,
        selectbackground=ACCENT,
        selectforeground="#0b1220",
        relief="flat",
        highlightthickness=0,
        font=("Segoe UI", 10),
    )
    listbox.grid(row=0, column=0, sticky="nsew")

    scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=listbox.yview)
    scrollbar.grid(row=0, column=1, sticky="ns")
    listbox.configure(yscrollcommand=scrollbar.set)

    for index, option in enumerate(options):
        listbox.insert("end", option)
        if option in selected_values:
            listbox.selection_set(index)

    buttons = tk.Frame(body, bg=BG_APP)
    buttons.grid(row=2, column=0, sticky="e", pady=(10, 0))

    def aplicar() -> None:
        valores = {options[idx] for idx in listbox.curselection()}
        on_apply(valores)
        dialog.destroy()

    btn_clear = tk.Button(
        buttons,
        text="Limpar",
        command=lambda: listbox.selection_clear(0, "end"),
        bg="#334155",
        fg=TEXT_PRIMARY,
        activebackground="#475569",
        activeforeground=TEXT_PRIMARY,
        relief="flat",
        bd=0,
        cursor="hand2",
        padx=12,
        pady=8,
        font=("Segoe UI", 10, "bold"),
    )
    btn_clear.pack(side="left", padx=(0, 8))
    style_hover_button(btn_clear, "#334155", "#475569")

    btn_apply = tk.Button(
        buttons,
        text="Aplicar",
        command=aplicar,
        bg="#0f172a",
        fg=TEXT_PRIMARY,
        activebackground=ACCENT,
        activeforeground="#0b1220",
        relief="flat",
        bd=0,
        cursor="hand2",
        padx=12,
        pady=8,
        font=("Segoe UI", 10, "bold"),
    )
    btn_apply.pack(side="left", padx=(0, 8))
    style_hover_button(btn_apply, "#0f172a", "#1e293b")

    btn_close = tk.Button(
        buttons,
        text="Fechar",
        command=dialog.destroy,
        bg="#334155",
        fg=TEXT_PRIMARY,
        activebackground="#475569",
        activeforeground=TEXT_PRIMARY,
        relief="flat",
        bd=0,
        cursor="hand2",
        padx=12,
        pady=8,
        font=("Segoe UI", 10, "bold"),
    )
    btn_close.pack(side="left")
    style_hover_button(btn_close, "#334155", "#475569")

    dialog.wait_window()


def choose_export_format(parent: tk.Toplevel) -> str | None:
    dialog = tk.Toplevel(parent)
    dialog.title("Tipo de exportação")
    dialog.geometry("360x180")
    dialog.minsize(360, 180)
    dialog.transient(parent)
    dialog.grab_set()
    dialog.configure(bg=BG_APP)

    selected_format: str | None = None

    def select_and_close(value: str | None) -> None:
        nonlocal selected_format
        selected_format = value
        dialog.destroy()

    dialog.protocol("WM_DELETE_WINDOW", lambda: select_and_close(None))

    body = tk.Frame(dialog, bg=BG_APP, padx=14, pady=14)
    body.pack(fill="both", expand=True)
    body.grid_rowconfigure(1, weight=1)
    body.grid_columnconfigure(0, weight=1)

    tk.Label(
        body,
        text="Selecione o formato de exportação",
        bg=BG_APP,
        fg=TEXT_PRIMARY,
        font=("Segoe UI", 11, "bold"),
    ).grid(row=0, column=0, sticky="w", pady=(0, 12))

    buttons = tk.Frame(body, bg=BG_APP)
    buttons.grid(row=1, column=0, sticky="e")

    btn_excel = tk.Button(
        buttons,
        text="Excel (.xlsx)",
        command=lambda: select_and_close("excel"),
        bg="#0f172a",
        fg=TEXT_PRIMARY,
        activebackground=ACCENT,
        activeforeground="#0b1220",
        relief="flat",
        bd=0,
        cursor="hand2",
        padx=12,
        pady=8,
        font=("Segoe UI", 10, "bold"),
    )
    btn_excel.pack(side="left", padx=(0, 8))
    style_hover_button(btn_excel, "#0f172a", "#1e293b")

    btn_text = tk.Button(
        buttons,
        text="Texto (.txt)",
        command=lambda: select_and_close("texto"),
        bg="#0f172a",
        fg=TEXT_PRIMARY,
        activebackground=ACCENT,
        activeforeground="#0b1220",
        relief="flat",
        bd=0,
        cursor="hand2",
        padx=12,
        pady=8,
        font=("Segoe UI", 10, "bold"),
    )
    btn_text.pack(side="left", padx=(0, 8))
    style_hover_button(btn_text, "#0f172a", "#1e293b")

    btn_cancel = tk.Button(
        buttons,
        text="Cancelar",
        command=lambda: select_and_close(None),
        bg="#334155",
        fg=TEXT_PRIMARY,
        activebackground="#475569",
        activeforeground=TEXT_PRIMARY,
        relief="flat",
        bd=0,
        cursor="hand2",
        padx=12,
        pady=8,
        font=("Segoe UI", 10, "bold"),
    )
    btn_cancel.pack(side="left")
    style_hover_button(btn_cancel, "#334155", "#475569")

    dialog.wait_window()
    return selected_format


def export_rows(rows: list[dict[str, object]], columns: tuple[str, ...], parent: tk.Toplevel) -> None:
    if not rows:
        messagebox.showinfo("Exportação", "Não há dados em tela para exportar.", parent=parent)
        return

    export_format = choose_export_format(parent)
    if export_format is None:
        return

    if export_format == "excel":
        file_path = filedialog.asksaveasfilename(
            parent=parent,
            title="Exportar para Excel",
            defaultextension=".xlsx",
            filetypes=[("Excel", "*.xlsx")],
        )
        if not file_path:
            return
        try:
            from openpyxl import Workbook

            workbook = Workbook()
            sheet = workbook.active
            sheet.title = "Resultado"
            sheet.append(list(columns))
            for row in rows:
                sheet.append([row.get(column, "") for column in columns])
            workbook.save(file_path)
        except Exception as exc:
            messagebox.showerror("Erro ao exportar", str(exc), parent=parent)
            return
    elif export_format == "texto":
        file_path = filedialog.asksaveasfilename(
            parent=parent,
            title="Exportar para texto",
            defaultextension=".txt",
            filetypes=[("Texto", "*.txt")],
        )
        if not file_path:
            return
        try:
            with open(file_path, "w", encoding="utf-8") as file:
                file.write("\t".join(columns) + "\n")
                for row in rows:
                    file.write("\t".join(str(row.get(column, "")) for column in columns) + "\n")
        except Exception as exc:
            messagebox.showerror("Erro ao exportar", str(exc), parent=parent)
            return
    else:
        return

    messagebox.showinfo("Exportação", "Arquivo exportado com sucesso.", parent=parent)


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
    tree, _, _ = create_tree_with_scrollbars(list_frame, columns)

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
            messagebox.showerror("Dados inválidos", "ID e Procfit devem ser números inteiros.", parent=modal)
            return
        nome = nome_var.get().strip()
        nome_fantasia = nome_fantasia_var.get().strip()
        if not nome or not nome_fantasia:
            messagebox.showerror("Dados inválidos", "Preencha Nome e Nome Fantasia.", parent=modal)
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
    tree, _, _ = create_tree_with_scrollbars(list_frame, columns)

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
            messagebox.showerror("Dados inválidos", "CodRepres, Cod Forn e Cod Marca devem ser números inteiros.", parent=modal)
            return

        nome = vars_map["Nome"].get().strip()
        login = vars_map["Login"].get().strip()
        fornecedor = vars_map["Fornecedor"].get().strip()
        marca = vars_map["Marca"].get().strip()
        if not nome or not login or not fornecedor or not marca:
            messagebox.showerror("Dados inválidos", "Preencha todos os campos de texto.", parent=modal)
            return
        if not is_valid_email(login):
            messagebox.showerror("Dados inválidos", "Login deve estar no formato de e-mail.", parent=modal)
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
        ("E-mail/Usuário", email_var, 1, 0),
        ("Ações", acoes_var, 1, 2),
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

    tk.Label(form, text="Situação", bg=BG_SURFACE, fg=TEXT_PRIMARY, font=("Segoe UI", 10, "bold")).grid(
        row=2, column=0, sticky="w", padx=(0, 8), pady=4
    )
    cmb_situacao = ttk.Combobox(form, textvariable=situacao_var, values=("Ativo", "Inativo"), state="readonly")
    cmb_situacao.grid(row=2, column=1, sticky="ew", padx=(0, 12), pady=4, ipady=2)

    list_frame = tk.Frame(content, bg=BG_SURFACE)
    list_frame.grid(row=2, column=0, sticky="nsew")
    list_frame.grid_rowconfigure(0, weight=1)
    list_frame.grid_columnconfigure(0, weight=1)

    columns = ("D", "Nome", "E-mail/Usuário", "Situação", "Ações")
    tree, _, _ = create_tree_with_scrollbars(list_frame, columns)

    for col in columns:
        tree.heading(col, text=col)
    tree.column("D", width=70, anchor="center")
    tree.column("Nome", width=180, anchor="w")
    tree.column("E-mail/Usuário", width=240, anchor="w")
    tree.column("Situação", width=100, anchor="center")
    tree.column("Ações", width=220, anchor="w")

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
                values=(row["D"], row["Nome"], row["E-mail/Usuário"], row["Situação"], row["Ações"]),
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
            messagebox.showerror("Dados inválidos", "D deve ser número inteiro.", parent=modal)
            return

        nome = nome_var.get().strip()
        email = email_var.get().strip()
        situacao = situacao_var.get().strip()
        acoes = acoes_var.get().strip()
        if not nome or not email or not acoes:
            messagebox.showerror("Dados inválidos", "Preencha Nome, E-mail/Usuário e Ações.", parent=modal)
            return
        if not is_valid_email(email):
            messagebox.showerror("Dados inválidos", "E-mail/Usuário deve estar no formato de e-mail.", parent=modal)
            return
        if situacao not in ("Ativo", "Inativo"):
            messagebox.showerror("Dados inválidos", "Situação deve ser Ativo ou Inativo.", parent=modal)
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


def show_relatorio_contatos_modal(parent: tk.Tk) -> None:
    modal, body, content = create_modal(parent, "Relatório de Contatos")

    filter_row = tk.Frame(content, bg=BG_SURFACE)
    filter_row.grid(row=0, column=0, sticky="ew", pady=(0, 10))
    for idx in range(4):
        filter_row.grid_columnconfigure(idx * 2 + 1, weight=1)

    summary_label = tk.Label(
        filter_row,
        text="Registros relacionados: 0",
        bg=BG_SURFACE,
        fg=TEXT_SECONDARY,
        font=("Segoe UI", 9, "bold"),
    )
    summary_label.grid(row=2, column=0, columnspan=8, sticky="w", pady=(6, 0))

    list_frame = tk.Frame(content, bg=BG_SURFACE)
    list_frame.grid(row=2, column=0, sticky="nsew")
    list_frame.grid_rowconfigure(0, weight=1)
    list_frame.grid_columnconfigure(0, weight=1)

    columns = (
        "Contato",
        "E-mail/Usuário",
        "Situação",
        "Representante",
        "Fabricante",
        "Nome Fantasia",
        "Marca",
    )
    tree, _, _ = create_tree_with_scrollbars(list_frame, columns)

    widths = {
        "Contato": 160,
        "E-mail/Usuário": 220,
        "Situação": 90,
        "Representante": 180,
        "Fabricante": 220,
        "Nome Fantasia": 160,
        "Marca": 160,
    }
    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, width=widths[col], anchor="w")

    raw_rows = database.fetch_relatorio_contatos()
    filter_specs = (
        ("Contato", "Contato"),
        ("Situação", "Situação"),
        ("Representante", "Representante"),
        ("Fabricante", "Fabricante"),
        ("Nome Fantasia", "Nome Fantasia"),
        ("Marca", "Marca"),
        ("E-mail/Usuário", "E-mail/Usuário"),
    )
    filter_vars: dict[str, tk.StringVar] = {}
    filter_boxes: list[ttk.Combobox] = []

    for idx, (label_text, row_key) in enumerate(filter_specs):
        row_no = idx // 4
        col_no = (idx % 4) * 2
        tk.Label(
            filter_row,
            text=label_text,
            bg=BG_SURFACE,
            fg=TEXT_PRIMARY,
            font=("Segoe UI", 10, "bold"),
        ).grid(row=row_no, column=col_no, sticky="w", padx=(0, 8), pady=4)

        values = ["Todos"] + sorted({str(row[row_key]) for row in raw_rows})
        filter_var = tk.StringVar(value="Todos")
        filter_vars[row_key] = filter_var
        filter_box = ttk.Combobox(filter_row, textvariable=filter_var, values=values, state="readonly")
        filter_box.grid(row=row_no, column=col_no + 1, sticky="ew", padx=(0, 12), pady=4, ipady=2)
        filter_boxes.append(filter_box)

    def refresh_tree(*_args: object) -> None:
        rows = raw_rows
        for row_key, filter_var in filter_vars.items():
            selected_value = filter_var.get().strip()
            if selected_value and selected_value != "Todos":
                rows = [row for row in rows if str(row[row_key]) == selected_value]
        for item in tree.get_children():
            tree.delete(item)
        for row in rows:
            tree.insert(
                "",
                "end",
                values=(
                    row["Contato"],
                    row["E-mail/Usuário"],
                    row["Situação"],
                    row["Representante"],
                    row["Fabricante"],
                    row["Nome Fantasia"],
                    row["Marca"],
                ),
            )
        summary_label.config(text=f"Registros relacionados: {len(rows)}")

    for filter_box in filter_boxes:
        filter_box.bind("<<ComboboxSelected>>", refresh_tree)
    create_action_buttons(body, refresh_tree, modal.destroy)
    refresh_tree()
    modal.wait_window()


def show_relatorio_contatos_produtos_modal(parent: tk.Tk) -> None:
    modal, body, content = create_modal(parent, "Relatório de Contatos x Produtos")

    filter_row = tk.Frame(content, bg=BG_SURFACE)
    filter_row.grid(row=0, column=0, sticky="ew", pady=(0, 10))
    for idx in range(3):
        filter_row.grid_columnconfigure(idx * 2 + 1, weight=1)

    summary_label = tk.Label(
        filter_row,
        text="Registros em tela: 0",
        bg=BG_SURFACE,
        fg=TEXT_SECONDARY,
        font=("Segoe UI", 9, "bold"),
    )
    summary_label.grid(row=2, column=0, columnspan=6, sticky="w", pady=(8, 0))

    list_frame = tk.Frame(content, bg=BG_SURFACE)
    list_frame.grid(row=2, column=0, sticky="nsew")
    list_frame.grid_rowconfigure(0, weight=1)
    list_frame.grid_columnconfigure(0, weight=1)

    columns = (
        "Nome",
        "E-mail/Usuário",
        "CD_FORNEC",
        "Nome Fantasia",
        "MARCA",
        "CD_PROD",
        "EAN",
        "DESCRICAO",
        "VALOR UNITARIO",
        "FATOR EMBALAGEM",
    )
    tree, _, _ = create_tree_with_scrollbars(list_frame, columns)

    widths = {
        "Nome": 180,
        "E-mail/Usuário": 240,
        "CD_FORNEC": 90,
        "Nome Fantasia": 180,
        "MARCA": 170,
        "CD_PROD": 90,
        "EAN": 130,
        "DESCRICAO": 320,
        "VALOR UNITARIO": 120,
        "FATOR EMBALAGEM": 130,
    }
    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, width=widths[col], anchor="w")

    try:
        raw_rows = database.fetch_relatorio_contatos_produtos()
    except Exception as exc:
        messagebox.showerror("Erro ao consultar", str(exc), parent=modal)
        modal.destroy()
        return

    filter_specs = (
        ("Contato", "Nome"),
        ("Fornecedor", "Nome Fantasia"),
        ("Marca", "MARCA"),
        ("Descrição", "DESCRICAO"),
    )
    filter_state = {row_key: set() for _, row_key in filter_specs}
    filter_labels: dict[str, tk.Label] = {}
    current_rows: list[dict[str, object]] = []

    for idx, (label_text, row_key) in enumerate(filter_specs):
        row_no = idx // 3
        col_no = (idx % 3) * 2

        tk.Label(
            filter_row,
            text=label_text,
            bg=BG_SURFACE,
            fg=TEXT_PRIMARY,
            font=("Segoe UI", 10, "bold"),
        ).grid(row=row_no, column=col_no, sticky="w", padx=(0, 8), pady=4)

        cell = tk.Frame(filter_row, bg=BG_SURFACE)
        cell.grid(row=row_no, column=col_no + 1, sticky="ew", padx=(0, 12), pady=4)
        cell.grid_columnconfigure(0, weight=1)

        summary = tk.Label(
            cell,
            text="Todos",
            bg=BG_SURFACE,
            fg=TEXT_SECONDARY,
            anchor="w",
            font=("Segoe UI", 9),
        )
        summary.grid(row=0, column=0, sticky="ew")
        filter_labels[row_key] = summary

        options = sorted({str(row.get(row_key, "")) for row in raw_rows})

        def make_open_filter(key: str, title: str, available_options: list[str]) -> callable:
            def open_filter() -> None:
                open_multi_select_dialog(
                    modal,
                    f"Filtro: {title}",
                    available_options,
                    filter_state[key],
                    lambda values: apply_filter(key, values),
                )
            return open_filter

        btn_filter = tk.Button(
            cell,
            text="Selecionar",
            command=make_open_filter(row_key, label_text, options),
            bg="#0f172a",
            fg=TEXT_PRIMARY,
            activebackground=ACCENT,
            activeforeground="#0b1220",
            relief="flat",
            bd=0,
            cursor="hand2",
            padx=8,
            pady=6,
            font=("Segoe UI", 9, "bold"),
        )
        btn_filter.grid(row=1, column=0, sticky="w", pady=(4, 0))
        style_hover_button(btn_filter, "#0f172a", "#1e293b")

    def refresh_tree() -> None:
        rows = raw_rows
        for row_key, selected_values in filter_state.items():
            if selected_values:
                rows = [row for row in rows if str(row.get(row_key, "")) in selected_values]

        current_rows.clear()
        current_rows.extend(rows)

        for item in tree.get_children():
            tree.delete(item)

        for row in rows:
            tree.insert("", "end", values=tuple(row.get(column, "") for column in columns))

        summary_label.config(text=f"Registros em tela: {len(rows)}")

    def apply_filter(row_key: str, values: set[str]) -> None:
        filter_state[row_key] = values
        filter_labels[row_key].config(text=summarize_selected_values(values))
        refresh_tree()

    footer = tk.Frame(body, bg=BG_APP)
    footer.grid(row=2, column=0, sticky="ew", pady=(10, 0))
    footer.grid_columnconfigure(0, weight=1)

    footer_buttons = tk.Frame(footer, bg=BG_APP)
    footer_buttons.grid(row=0, column=0, sticky="e")

    btn_export = tk.Button(
        footer_buttons,
        text="Exportar",
        command=lambda: export_rows(current_rows, columns, modal),
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
    btn_export.pack(side="left", padx=(0, 8))
    style_hover_button(btn_export, "#1f3b2d", "#2f5f45")

    btn_close = tk.Button(
        footer_buttons,
        text="Fechar",
        command=modal.destroy,
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
        text="Sistema de Cotação",
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
        text="Ações",
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
        title_label.config(text="Ações")
        clear_frame(actions_body)
        card = tk.Frame(actions_body, bg="#172033", highlightthickness=1, highlightbackground="#334155")
        card.grid(row=0, column=0, sticky="nsew")
        card.grid_columnconfigure(0, weight=1)
        card.grid_rowconfigure(0, weight=1)
        style_hover_frame(card, "#172033", BG_SURFACE_HOVER)

        btn_relatorio_produtos = tk.Button(
            card,
            text="Selecionar Produtos",
            command=lambda: show_relatorio_contatos_produtos_modal(root),
            bg="#0f172a",
            fg=TEXT_PRIMARY,
            activebackground=ACCENT,
            activeforeground="#0b1220",
            relief="flat",
            bd=0,
            cursor="hand2",
            padx=10,
            pady=9,
            font=("Segoe UI", 10, "bold"),
        )
        btn_relatorio_produtos.grid(row=0, column=0, sticky="nw", padx=12, pady=12)
        style_hover_button(btn_relatorio_produtos, "#0f172a", "#1e293b")

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

    tk.Label(
        cadastros_col,
        text="Relatório",
        bg=BG_SURFACE,
        fg=ACCENT,
        anchor="w",
        font=("Segoe UI", 11, "bold"),
    ).pack(fill="x", pady=(14, 10))

    btn_relatorio_contatos = tk.Button(
        cadastros_col,
        text="De Contatos",
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
        command=lambda: show_relatorio_contatos_modal(root),
    )
    btn_relatorio_contatos.pack(fill="x", pady=4)
    style_hover_button(btn_relatorio_contatos, "#0f172a", "#1e293b")

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
