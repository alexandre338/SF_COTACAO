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


def configure_tree_columns(
    tree: ttk.Treeview,
    columns: tuple[str, ...],
    widths: dict[str, int],
    headings: dict[str, str] | None = None,
) -> None:
    headings = headings or {}
    for col in columns:
        tree.heading(col, text=headings.get(col, col))
        tree.column(col, width=widths[col], anchor="w")


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


def parse_clipboard_table(clipboard_text: str, expected_columns: tuple[str, ...]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    normalized_expected = [column.strip().casefold() for column in expected_columns]

    for line_index, line in enumerate(clipboard_text.splitlines()):
        if not line.strip():
            continue
        values = [value.strip() for value in line.split("\t")]
        normalized_values = [value.casefold() for value in values[: len(expected_columns)]]
        if line_index == 0 and normalized_values == normalized_expected:
            continue
        if len(values) < len(expected_columns):
            values.extend([""] * (len(expected_columns) - len(values)))
        elif len(values) > len(expected_columns):
            values = values[: len(expected_columns)]
        rows.append(dict(zip(expected_columns, values)))
    return rows


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


def show_cotacoes_captadas_modal(parent: tk.Tk) -> None:
    modal, body, content = create_modal(parent, "Carga de Cotacoes")

    filter_row = tk.Frame(content, bg=BG_SURFACE)
    filter_row.grid(row=0, column=0, sticky="ew", pady=(0, 10))
    for idx in range(2):
        filter_row.grid_columnconfigure(idx * 2 + 1, weight=1)

    tk.Label(
        filter_row,
        text='Cole da planilha Excel usando Ctrl+C e use "Colar da Area de Transferencia".',
        bg=BG_SURFACE,
        fg=TEXT_SECONDARY,
        anchor="w",
        font=("Segoe UI", 9),
    ).grid(row=0, column=0, columnspan=4, sticky="w", pady=(0, 10))

    list_frame = tk.Frame(content, bg=BG_SURFACE)
    list_frame.grid(row=2, column=0, sticky="nsew")
    list_frame.grid_rowconfigure(0, weight=1)
    list_frame.grid_columnconfigure(0, weight=1)

    columns = (
        "Nome",
        "E-mail/Usuario",
        "CD_FORNEC",
        "Nome Fantasia",
        "MARCA",
        "CD_PROD",
        "EAN",
        "DESCRICAO",
        "VALOR UNITARIO",
        "FATOR EMBALAGEM",
        "VALIDADE PRECO",
    )
    tree, _, _ = create_tree_with_scrollbars(list_frame, columns)
    configure_tree_columns(
        tree,
        columns,
        {
            "Nome": 180,
            "E-mail/Usuario": 240,
            "CD_FORNEC": 90,
            "Nome Fantasia": 180,
            "MARCA": 170,
            "CD_PROD": 90,
            "EAN": 130,
            "DESCRICAO": 320,
            "VALOR UNITARIO": 120,
            "FATOR EMBALAGEM": 130,
            "VALIDADE PRECO": 120,
        },
    )

    raw_rows = database.fetch_cotacoes_captadas()
    current_rows: list[dict[str, object]] = []
    filter_specs = (
        ("Nome Fantasia", "Nome Fantasia"),
        ("Validade Preco", "VALIDADE PRECO"),
    )
    filter_state = {row_key: set() for _, row_key in filter_specs}
    filter_labels: dict[str, tk.Label] = {}
    filter_options: dict[str, list[str]] = {row_key: [] for _, row_key in filter_specs}

    for idx, (label_text, row_key) in enumerate(filter_specs):
        col_no = idx * 2
        tk.Label(filter_row, text=label_text, bg=BG_SURFACE, fg=TEXT_PRIMARY, font=("Segoe UI", 10, "bold")).grid(
            row=1, column=col_no, sticky="w", padx=(0, 8), pady=4
        )
        cell = tk.Frame(filter_row, bg=BG_SURFACE)
        cell.grid(row=1, column=col_no + 1, sticky="ew", padx=(0, 12), pady=4)
        cell.grid_columnconfigure(0, weight=1)
        summary = tk.Label(cell, text="Todos", bg=BG_SURFACE, fg=TEXT_SECONDARY, anchor="w", font=("Segoe UI", 9))
        summary.grid(row=0, column=0, sticky="ew")
        filter_labels[row_key] = summary

        def make_open_filter(key: str, title: str) -> callable:
            def open_filter() -> None:
                open_multi_select_dialog(modal, f"Filtro: {title}", filter_options[key], filter_state[key], lambda values: apply_filter(key, values))

            return open_filter

        btn_filter = tk.Button(
            cell,
            text="Selecionar",
            command=make_open_filter(row_key, label_text),
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

    summary_label = tk.Label(filter_row, text="Registros carregados: 0", bg=BG_SURFACE, fg=TEXT_SECONDARY, font=("Segoe UI", 9, "bold"))
    summary_label.grid(row=2, column=0, columnspan=3, sticky="w", pady=(8, 0))

    def refresh_tree() -> None:
        nonlocal raw_rows
        raw_rows = database.fetch_cotacoes_captadas()
        for _, row_key in filter_specs:
            available_options = sorted({str(row.get(row_key, "")) for row in raw_rows})
            filter_options[row_key] = available_options
            filter_state[row_key] = {value for value in filter_state[row_key] if value in available_options}
            filter_labels[row_key].config(text=summarize_selected_values(filter_state[row_key]))

        rows = raw_rows
        for _, row_key in filter_specs:
            if filter_state[row_key]:
                rows = [row for row in rows if str(row.get(row_key, "")) in filter_state[row_key]]

        current_rows.clear()
        current_rows.extend(rows)

        for item in tree.get_children():
            tree.delete(item)
        for row in rows:
            tree.insert("", "end", values=tuple(row.get(column, "") for column in columns))
        summary_label.config(text=f"Registros carregados: {len(rows)}")

    def apply_filter(row_key: str, values: set[str]) -> None:
        filter_state[row_key] = values
        refresh_tree()

    def clear_filters() -> None:
        for _, row_key in filter_specs:
            filter_state[row_key] = set()
        refresh_tree()

    def carregar_area_transferencia() -> None:
        try:
            clipboard_text = modal.clipboard_get()
        except tk.TclError:
            messagebox.showerror("Area de transferencia", "Nao ha conteudo de texto na area de transferencia.", parent=modal)
            return

        rows = parse_clipboard_table(clipboard_text, columns)
        if not rows:
            messagebox.showerror("Dados invalidos", "Nenhuma linha valida foi encontrada para carregar.", parent=modal)
            return

        invalid_rows: list[int] = []
        saved_count = 0
        for idx, row in enumerate(rows, start=1):
            if not row["Nome"] or not row["E-mail/Usuario"] or not row["EAN"] or not row["DESCRICAO"]:
                invalid_rows.append(idx)
                continue
            try:
                database.upsert_cotacao_captada(row)
                saved_count += 1
            except Exception:
                invalid_rows.append(idx)

        refresh_tree()
        if invalid_rows:
            messagebox.showwarning("Carga parcial", f"{saved_count} registro(s) gravado(s). Linhas ignoradas: {', '.join(str(n) for n in invalid_rows)}.", parent=modal)
            return
        messagebox.showinfo("Carga concluida", f"{saved_count} registro(s) gravado(s) com sucesso.", parent=modal)

    def limpar_dados() -> None:
        if not current_rows:
            messagebox.showinfo("Limpar Dados", "Nao ha registros filtrados na tela para apagar.", parent=modal)
            return
        if not messagebox.askyesno("Limpar Dados", f"Deseja apagar {len(current_rows)} registro(s) exibido(s)?", parent=modal):
            return
        deleted_count = database.delete_cotacoes_captadas(current_rows)
        refresh_tree()
        messagebox.showinfo("Limpar Dados", f"{deleted_count} registro(s) apagado(s).", parent=modal)

    footer = tk.Frame(body, bg=BG_APP)
    footer.grid(row=2, column=0, sticky="ew", pady=(10, 0))
    footer.grid_columnconfigure(0, weight=1)
    footer_buttons = tk.Frame(footer, bg=BG_APP)
    footer_buttons.grid(row=0, column=0, sticky="e")

    button_specs = (
        ("Colar da Area de Transferencia", carregar_area_transferencia, "#1f3b2d", "#2f5f45"),
        ("Atualizar", refresh_tree, "#0f172a", "#1e293b"),
        ("Limpar Dados", limpar_dados, "#7f1d1d", "#991b1b"),
        ("Limpar Filtros", clear_filters, "#334155", "#475569"),
        ("Fechar", modal.destroy, "#334155", "#475569"),
    )
    for text, command, bg_color, hover_color in button_specs:
        btn = tk.Button(
            footer_buttons,
            text=text,
            command=command,
            bg=bg_color,
            fg=TEXT_PRIMARY,
            activebackground=hover_color if bg_color != "#0f172a" else ACCENT,
            activeforeground=TEXT_PRIMARY if bg_color != "#0f172a" else "#0b1220",
            relief="flat",
            bd=0,
            cursor="hand2",
            padx=14,
            pady=8,
            font=("Segoe UI", 10, "bold"),
        )
        btn.pack(side="left", padx=(0, 8))
        style_hover_button(btn, bg_color, hover_color)

    refresh_tree()
    modal.wait_window()


def show_cs_compara_01_modal(parent: tk.Tk) -> None:
    modal, body, content = create_modal(parent, "Analise CS_COMPARA_01")

    filter_row = tk.Frame(content, bg=BG_SURFACE)
    filter_row.grid(row=0, column=0, sticky="ew", pady=(0, 10))
    for idx in range(4):
        filter_row.grid_columnconfigure(idx * 2 + 1, weight=1)

    list_frame = tk.Frame(content, bg=BG_SURFACE)
    list_frame.grid(row=2, column=0, sticky="nsew")
    list_frame.grid_rowconfigure(0, weight=1)
    list_frame.grid_columnconfigure(0, weight=1)

    columns = (
        "CD_PROD",
        "EAN",
        "DESCRICAO",
        "VALOR UNITARIO",
        "FATOR EMBALAGEM",
        "VALIDADE PRECO",
        "ultimo_custo",
        "valida_data",
        "valor_cotado",
        "compara_ult_custo",
        "div_custo",
        "ult_entrada_data",
        "cod_produto",
        "Nome",
        "E-mail/Usuario",
        "CD_FORNEC",
        "Nome Fantasia",
        "MARCA",
    )
    tree, _, _ = create_tree_with_scrollbars(list_frame, columns)
    configure_tree_columns(tree, columns, {column: 130 for column in columns} | {"DESCRICAO": 260, "E-mail/Usuario": 220, "Nome Fantasia": 160})

    raw_rows = database.fetch_cs_compara_01()
    filter_specs = (
        ("Fornecedor", "Nome Fantasia"),
        ("Validacao", "valida_data"),
        ("Divergencia", "div_custo"),
        ("Marca", "MARCA"),
    )
    filter_state = {row_key: set() for _, row_key in filter_specs}
    filter_labels: dict[str, tk.Label] = {}
    current_rows: list[dict[str, object]] = []
    filter_options: dict[str, list[str]] = {row_key: [] for _, row_key in filter_specs}

    for idx, (label_text, row_key) in enumerate(filter_specs):
        col_no = idx * 2
        tk.Label(filter_row, text=label_text, bg=BG_SURFACE, fg=TEXT_PRIMARY, font=("Segoe UI", 10, "bold")).grid(
            row=0, column=col_no, sticky="w", padx=(0, 8), pady=4
        )
        cell = tk.Frame(filter_row, bg=BG_SURFACE)
        cell.grid(row=0, column=col_no + 1, sticky="ew", padx=(0, 12), pady=4)
        cell.grid_columnconfigure(0, weight=1)
        summary = tk.Label(cell, text="Todos", bg=BG_SURFACE, fg=TEXT_SECONDARY, anchor="w", font=("Segoe UI", 9))
        summary.grid(row=0, column=0, sticky="ew")
        filter_labels[row_key] = summary

        def make_open_filter(key: str, title: str) -> callable:
            def open_filter() -> None:
                open_multi_select_dialog(modal, f"Filtro: {title}", filter_options[key], filter_state[key], lambda values: apply_filter(key, values))

            return open_filter

        btn = tk.Button(
            cell,
            text="Selecionar",
            command=make_open_filter(row_key, label_text),
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
        btn.grid(row=1, column=0, sticky="w", pady=(4, 0))
        style_hover_button(btn, "#0f172a", "#1e293b")

    summary_label = tk.Label(filter_row, text="Registros em tela: 0", bg=BG_SURFACE, fg=TEXT_SECONDARY, font=("Segoe UI", 9, "bold"))
    summary_label.grid(row=1, column=0, columnspan=7, sticky="w", pady=(10, 0))

    def refresh_tree() -> None:
        for _, row_key in filter_specs:
            filter_options[row_key] = sorted({str(row.get(row_key, "")) for row in raw_rows})
            filter_labels[row_key].config(text=summarize_selected_values(filter_state[row_key]))
        rows = raw_rows
        for _, row_key in filter_specs:
            if filter_state[row_key]:
                rows = [row for row in rows if str(row.get(row_key, "")) in filter_state[row_key]]
        current_rows.clear()
        current_rows.extend(rows)
        for item in tree.get_children():
            tree.delete(item)
        for row in rows:
            tree.insert("", "end", values=tuple(row.get(column, "") for column in columns))
        summary_label.config(text=f"Registros em tela: {len(rows)}")

    def apply_filter(row_key: str, values: set[str]) -> None:
        filter_state[row_key] = values
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


def show_cs_compara_fornec_modal(parent: tk.Tk) -> None:
    modal, body, content = create_modal(parent, "Comparar Valores")

    filter_row = tk.Frame(content, bg=BG_SURFACE)
    filter_row.grid(row=0, column=0, sticky="ew", pady=(0, 10))
    filter_row.grid_columnconfigure(1, weight=1)
    filter_row.grid_columnconfigure(3, weight=1)

    list_frame = tk.Frame(content, bg=BG_SURFACE)
    list_frame.grid(row=1, column=0, sticky="nsew")
    list_frame.grid_rowconfigure(0, weight=1)
    list_frame.grid_columnconfigure(0, weight=1)

    payload = database.fetch_cs_compara_fornec()
    columns = tuple(str(col) for col in payload.get("columns", ()))
    source_rows = list(payload.get("rows", []))
    tree, _, _ = create_tree_with_scrollbars(list_frame, columns)
    configure_tree_columns(tree, columns, {column: 150 for column in columns} | {"DESCRICAO": 320, "Contato": 240, "Nome": 180})

    summary_label = tk.Label(body, text="Registros em tela: 0", bg=BG_APP, fg=TEXT_SECONDARY, font=("Segoe UI", 9, "bold"))
    summary_label.grid(row=0, column=0, sticky="e", pady=(0, 6))

    current_rows: list[dict[str, object]] = []
    fornecedor_filter_state: set[str] = set()
    representante_filter_state: set[str] = set()
    available_fornecedores = sorted({str(row.get("Fornecedor", "")).strip() for row in source_rows if str(row.get("Fornecedor", "")).strip()})
    available_representantes = sorted({str(row.get("Nome", "")).strip() for row in source_rows if str(row.get("Nome", "")).strip()})
    filter_summaries: dict[str, tk.Label] = {}

    for idx, (label_text, state_key, options) in enumerate(
        (
            ("Fornecedor", "fornecedor", available_fornecedores),
            ("Representante", "representante", available_representantes),
        )
    ):
        tk.Label(filter_row, text=label_text, bg=BG_SURFACE, fg=TEXT_PRIMARY, font=("Segoe UI", 10, "bold")).grid(
            row=0, column=idx * 2, sticky="w", padx=(0, 8), pady=4
        )
        cell = tk.Frame(filter_row, bg=BG_SURFACE)
        cell.grid(row=0, column=idx * 2 + 1, sticky="ew", padx=(0, 12), pady=4)
        cell.grid_columnconfigure(0, weight=1)
        summary = tk.Label(cell, text="Todos", bg=BG_SURFACE, fg=TEXT_SECONDARY, anchor="w", font=("Segoe UI", 9))
        summary.grid(row=0, column=0, sticky="ew")
        filter_summaries[state_key] = summary

        def make_open_filter(title: str, state_name: str, available_options: list[str]) -> callable:
            def open_filter() -> None:
                selected_values = fornecedor_filter_state if state_name == "fornecedor" else representante_filter_state
                open_multi_select_dialog(modal, f"Filtro: {title}", available_options, selected_values, lambda values: apply_filter(state_name, values))

            return open_filter

        btn = tk.Button(
            cell,
            text="Selecionar",
            command=make_open_filter(label_text, state_key, options),
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
        btn.grid(row=1, column=0, sticky="w", pady=(4, 0))
        style_hover_button(btn, "#0f172a", "#1e293b")

    def apply_filter(kind: str, values: set[str]) -> None:
        nonlocal fornecedor_filter_state, representante_filter_state
        if kind == "fornecedor":
            fornecedor_filter_state = values
        else:
            representante_filter_state = values
        refresh_tree()

    def refresh_tree() -> None:
        filtered_rows = source_rows
        if fornecedor_filter_state:
            filtered_rows = [row for row in filtered_rows if str(row.get("Fornecedor", "")).strip() in fornecedor_filter_state]
        if representante_filter_state:
            filtered_rows = [row for row in filtered_rows if str(row.get("Nome", "")).strip() in representante_filter_state]
        current_rows.clear()
        current_rows.extend(filtered_rows)
        filter_summaries["fornecedor"].config(text=summarize_selected_values(fornecedor_filter_state))
        filter_summaries["representante"].config(text=summarize_selected_values(representante_filter_state))
        for item in tree.get_children():
            tree.delete(item)
        for row in filtered_rows:
            tree.insert("", "end", values=tuple(row.get(column, "") for column in columns))
        summary_label.config(text=f"Registros em tela: {len(filtered_rows)}")

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


def show_conexoes_modal(parent: tk.Tk) -> None:
    modal, body, content = create_modal(parent, "Configurações de Conexão")
    modal.geometry("860x430")
    modal.minsize(860, 430)

    form = tk.Frame(content, bg=BG_SURFACE)
    form.grid(row=0, column=0, sticky="nsew")
    form.grid_columnconfigure(1, weight=1)
    form.grid_columnconfigure(3, weight=1)
    form.grid_columnconfigure(5, weight=1)
    form.grid_rowconfigure(3, weight=1)

    current = database.get_sqlserver_connection_settings()

    driver_var = tk.StringVar(value=str(current.get("driver", "")))
    host_var = tk.StringVar(value=str(current.get("host", "")))
    port_var = tk.StringVar(value=str(current.get("port", "")))
    database_var = tk.StringVar(value=str(current.get("database", "")))
    user_var = tk.StringVar(value=str(current.get("user", "")))
    password_var = tk.StringVar(value=str(current.get("password", "")))
    trust_var = tk.StringVar(value=str(current.get("trust_server_certificate", "yes")).lower())

    fields = (
        ("Driver ODBC", driver_var, 0, 0),
        ("Servidor", host_var, 0, 2),
        ("Porta", port_var, 0, 4),
        ("Banco de Dados", database_var, 1, 0),
        ("Usuário", user_var, 1, 2),
    )

    for label, var, row, col in fields:
        tk.Label(
            form,
            text=label,
            bg=BG_SURFACE,
            fg=TEXT_PRIMARY,
            font=("Segoe UI", 10, "bold"),
        ).grid(row=row, column=col, sticky="w", padx=(0, 8), pady=4)
        tk.Entry(
            form,
            textvariable=var,
            bg="#0f172a",
            fg=TEXT_PRIMARY,
            insertbackground=TEXT_PRIMARY,
            relief="flat",
            font=("Segoe UI", 10),
        ).grid(row=row, column=col + 1, sticky="ew", padx=(0, 12), pady=4, ipady=4)

    tk.Label(
        form,
        text="Senha",
        bg=BG_SURFACE,
        fg=TEXT_PRIMARY,
        font=("Segoe UI", 10, "bold"),
    ).grid(row=2, column=0, sticky="w", padx=(0, 8), pady=4)

    password_cell = tk.Frame(form, bg=BG_SURFACE)
    password_cell.grid(row=2, column=1, columnspan=3, sticky="ew", padx=(0, 12), pady=4)
    password_cell.grid_columnconfigure(0, weight=1)

    entry_password = tk.Entry(
        password_cell,
        textvariable=password_var,
        show="*",
        bg="#0f172a",
        fg=TEXT_PRIMARY,
        insertbackground=TEXT_PRIMARY,
        relief="flat",
        font=("Segoe UI", 10),
    )
    entry_password.grid(row=0, column=0, sticky="ew", ipady=4)

    btn_show_password = tk.Button(
        password_cell,
        text="Exibir Senha",
        bg="#334155",
        fg=TEXT_PRIMARY,
        activebackground="#475569",
        activeforeground=TEXT_PRIMARY,
        relief="flat",
        bd=0,
        cursor="hand2",
        padx=10,
        pady=7,
        font=("Segoe UI", 9, "bold"),
    )
    btn_show_password.grid(row=0, column=1, padx=(8, 0), sticky="e")
    style_hover_button(btn_show_password, "#334155", "#475569")

    def show_password(_event: object = None) -> None:
        entry_password.config(show="")

    def hide_password(_event: object = None) -> None:
        entry_password.config(show="*")

    btn_show_password.bind("<ButtonPress-1>", show_password)
    btn_show_password.bind("<ButtonRelease-1>", hide_password)
    btn_show_password.bind("<Leave>", hide_password)

    tk.Label(
        form,
        text="TrustServerCertificate",
        bg=BG_SURFACE,
        fg=TEXT_PRIMARY,
        font=("Segoe UI", 10, "bold"),
    ).grid(row=2, column=4, sticky="w", padx=(0, 8), pady=4)

    cmb_trust = ttk.Combobox(form, textvariable=trust_var, values=("yes", "no"), state="readonly")
    cmb_trust.grid(row=2, column=5, sticky="ew", padx=(0, 12), pady=4, ipady=2)

    hint = tk.Label(
        form,
        text="Exemplo: DRIVER=ODBC Driver 18 for SQL Server | Servidor=host ou IP | Porta=1433",
        bg=BG_SURFACE,
        fg=TEXT_SECONDARY,
        anchor="w",
        font=("Segoe UI", 9),
    )
    hint.grid(row=3, column=0, columnspan=6, sticky="sw", pady=(12, 0))

    def validate() -> bool:
        host = host_var.get().strip()
        db_name = database_var.get().strip()
        driver = driver_var.get().strip()
        port = port_var.get().strip()
        trust = trust_var.get().strip().lower()

        if not driver:
            messagebox.showerror("Dados inválidos", "Informe o Driver ODBC.", parent=modal)
            return False
        if not host:
            messagebox.showerror("Dados inválidos", "Informe o Servidor.", parent=modal)
            return False
        if not db_name:
            messagebox.showerror("Dados inválidos", "Informe o Banco de Dados.", parent=modal)
            return False
        if port and not port.isdigit():
            messagebox.showerror("Dados inválidos", "Porta deve conter apenas números.", parent=modal)
            return False
        if trust not in ("yes", "no"):
            messagebox.showerror("Dados inválidos", "TrustServerCertificate deve ser yes ou no.", parent=modal)
            return False
        return True

    def format_diagnostics(diag: dict[str, object]) -> str:
        drivers = diag.get("odbc_drivers", [])
        if isinstance(drivers, list):
            drivers_text = ", ".join(str(item) for item in drivers) if drivers else "(nenhum)"
        else:
            drivers_text = str(drivers)

        lines = [
            f"Executável empacotado: {'sim' if bool(diag.get('frozen')) else 'não'}",
            f"Python/EXE: {diag.get('python_executable', '')}",
            f"Pasta de dados: {diag.get('data_dir', '')}",
            f"Arquivo DB: {diag.get('db_path', '')}",
            f"Pasta gravável: {'sim' if bool(diag.get('data_dir_writable')) else 'não'}",
            f"pyodbc instalado: {'sim' if bool(diag.get('pyodbc_installed')) else 'não'}",
            f"Drivers ODBC: {drivers_text}",
        ]

        if diag.get("host"):
            reachable = diag.get("host_port_reachable")
            if reachable is True:
                net_status = "sim"
            elif reachable is False:
                net_status = "não"
            else:
                net_status = "não testado"
            lines.append(f"Host/porta acessível ({diag.get('host')}:{diag.get('port')}): {net_status}")

        if diag.get("data_dir_error"):
            lines.append(f"Erro pasta dados: {diag.get('data_dir_error')}")
        if diag.get("pyodbc_error"):
            lines.append(f"Erro pyodbc: {diag.get('pyodbc_error')}")
        if diag.get("host_port_error"):
            lines.append(f"Erro rede: {diag.get('host_port_error')}")

        return "\n".join(lines)

    def save_connection() -> None:
        if not validate():
            return
        payload = {
            "driver": driver_var.get().strip(),
            "host": host_var.get().strip(),
            "port": port_var.get().strip(),
            "database": database_var.get().strip(),
            "user": user_var.get().strip(),
            "password": password_var.get(),
            "trust_server_certificate": trust_var.get().strip().lower(),
        }
        try:
            database.save_sqlserver_connection_settings(payload)
            database.reset_legacy_adapter()
        except Exception as exc:
            messagebox.showerror("Erro ao salvar", str(exc), parent=modal)
            return
        messagebox.showinfo("Conexões", "Configuração de conexão salva com sucesso.", parent=modal)

    def test_connection() -> None:
        if not validate():
            return
        payload = {
            "driver": driver_var.get().strip(),
            "host": host_var.get().strip(),
            "port": port_var.get().strip(),
            "database": database_var.get().strip(),
            "user": user_var.get().strip(),
            "password": password_var.get(),
            "trust_server_certificate": trust_var.get().strip().lower(),
        }
        diagnostics = database.get_sqlserver_runtime_diagnostics(payload["host"], payload["port"])
        try:
            installed_drivers = diagnostics.get("odbc_drivers", [])
            if isinstance(installed_drivers, list):
                resolved_driver = database.resolve_sqlserver_driver(payload["driver"], [str(item) for item in installed_drivers])
                if not resolved_driver:
                    raise RuntimeError(
                        f"Driver ODBC '{payload['driver']}' não encontrado no Windows e nenhum driver SQL Server compatível foi localizado. "
                        "Instale ODBC Driver 17/18 for SQL Server ou selecione um driver existente."
                    )
                payload["driver"] = resolved_driver
                driver_var.set(resolved_driver)
            database.save_sqlserver_connection_settings(payload)
            database.reset_legacy_adapter()
            database.fetch_legado_marcas()
        except Exception as exc:
            messagebox.showerror(
                "Teste de conexão",
                f"Falha ao conectar:\n{exc}\n\nDiagnóstico técnico:\n{format_diagnostics(diagnostics)}",
                parent=modal,
            )
            return
        messagebox.showinfo(
            "Teste de conexão",
            f"Conexão realizada com sucesso.\n\nDiagnóstico técnico:\n{format_diagnostics(diagnostics)}",
            parent=modal,
        )

    footer = tk.Frame(body, bg=BG_APP)
    footer.grid(row=2, column=0, sticky="ew", pady=(10, 0))
    footer.grid_columnconfigure(0, weight=1)

    buttons = tk.Frame(footer, bg=BG_APP)
    buttons.grid(row=0, column=0, sticky="e")

    btn_test = tk.Button(
        buttons,
        text="Testar Conexão",
        command=test_connection,
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
    btn_test.pack(side="left", padx=(0, 8))
    style_hover_button(btn_test, "#1f3b2d", "#2f5f45")

    btn_save = tk.Button(
        buttons,
        text="Salvar",
        command=save_connection,
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
        buttons,
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
        card.grid_columnconfigure(0, weight=0)
        card.grid_columnconfigure(1, weight=1)
        card.grid_rowconfigure(0, weight=1)
        card.grid_rowconfigure(1, weight=1)
        style_hover_frame(card, "#172033", BG_SURFACE_HOVER)

        actions_list = tk.Frame(card, bg="#172033")
        actions_list.grid(row=0, column=0, rowspan=2, sticky="nw", padx=12, pady=12)

        btn_relatorio_produtos = tk.Button(
            actions_list,
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
            width=20,
        )
        btn_relatorio_produtos.pack(fill="x", pady=(0, 10))
        style_hover_button(btn_relatorio_produtos, "#0f172a", "#1e293b")

        btn_carregar_cotacoes = tk.Button(
            actions_list,
            text="Carregar Cotações",
            command=lambda: show_cotacoes_captadas_modal(root),
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
            width=20,
        )
        btn_carregar_cotacoes.pack(fill="x", pady=(0, 10))
        style_hover_button(btn_carregar_cotacoes, "#0f172a", "#1e293b")

        btn_cs_compara_01 = tk.Button(
            actions_list,
            text="Validação de Dados",
            command=lambda: show_cs_compara_01_modal(root),
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
            width=20,
        )
        btn_cs_compara_01.pack(fill="x", pady=(0, 10))
        style_hover_button(btn_cs_compara_01, "#0f172a", "#1e293b")

        btn_comparar_valores = tk.Button(
            actions_list,
            text="Comparar Valores",
            command=lambda: show_cs_compara_fornec_modal(root),
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
            width=20,
        )
        btn_comparar_valores.pack(fill="x")
        style_hover_button(btn_comparar_valores, "#0f172a", "#1e293b")

        settings_block = tk.Frame(
            card,
            bg="#0f172a",
            highlightthickness=1,
            highlightbackground="#334155",
        )
        settings_block.grid(row=1, column=1, sticky="se", padx=12, pady=12)

        tk.Label(
            settings_block,
            text="Configurações",
            bg="#0f172a",
            fg=ACCENT,
            anchor="w",
            padx=10,
            pady=8,
            font=("Segoe UI", 10, "bold"),
        ).pack(fill="x")

        btn_conexoes = tk.Button(
            settings_block,
            text="Conexões",
            command=lambda: show_conexoes_modal(root),
            bg="#111827",
            fg=TEXT_PRIMARY,
            activebackground=ACCENT,
            activeforeground="#0b1220",
            relief="flat",
            bd=0,
            cursor="hand2",
            padx=10,
            pady=8,
            font=("Segoe UI", 9, "bold"),
        )
        btn_conexoes.pack(fill="x", padx=8, pady=(0, 8))
        style_hover_button(btn_conexoes, "#111827", "#1f2937")

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
