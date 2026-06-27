"""
app.py - Fantasy League Manager: the graphical front-end (Stage E).

Run with:   python app.py
Requires:   psycopg2-binary, customtkinter   (see requirements.txt)

Screens
  * Connection  - connect to the PostgreSQL database (mydatabase)
  * Dashboard   - at-a-glance stats + top scorers
  * Tables      - full CRUD over every table, foreign keys shown as NAMES
  * Queries     - run Stage B queries (some interactive)
  * Programs    - run Stage D functions & procedures
"""
import os
import json
import tkinter as tk
from tkinter import messagebox

import customtkinter as ctk

import theme
import metadata as md
import programs as progs
from db import Database, DatabaseError
from widgets import DataGrid, RecordForm

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("green")

CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")


# --------------------------------------------------------------------------- #
def load_config():
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:
        from db import DEFAULT_SETTINGS
        return dict(DEFAULT_SETTINGS)


def save_config(cfg):
    try:
        with open(CONFIG_PATH, "w", encoding="utf-8") as fh:
            json.dump(cfg, fh, indent=2)
    except Exception:
        pass


# --------------------------------------------------------------------------- #
class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.db = Database()
        self.title("Fantasy League Manager")
        self.geometry("1200x760")
        self.minsize(1040, 660)
        self.configure(fg_color=theme.BG_DARK)

        theme.style_treeview(self)
        self.nav_buttons = {}
        self.content = None

        self._build_connect_screen()

    # ===================================================================== #
    #  Connection screen
    # ===================================================================== #
    def _build_connect_screen(self):
        self.connect_frame = ctk.CTkFrame(self, fg_color=theme.BG_DARK)
        self.connect_frame.pack(fill="both", expand=True)

        card = ctk.CTkFrame(self.connect_frame, fg_color=theme.BG_PANEL,
                            corner_radius=18, border_width=1, border_color=theme.BORDER)
        card.place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(card, text="⚽", font=theme.f(54)).pack(pady=(28, 0))
        ctk.CTkLabel(card, text="Fantasy League Manager",
                     font=theme.f(26, "bold"), text_color=theme.TEXT).pack(padx=60)
        ctk.CTkLabel(card, text="Premier League Fantasy  +  FIFA World Cup  ·  Stage E",
                     font=theme.f(12), text_color=theme.SUBTEXT).pack(pady=(2, 18))

        cfg = load_config()
        self.conn_entries = {}
        fields = [("host", "Host"), ("port", "Port"), ("dbname", "Database"),
                  ("user", "User"), ("password", "Password")]
        form = ctk.CTkFrame(card, fg_color="transparent")
        form.pack(padx=40, pady=4)
        for key, label in fields:
            row = ctk.CTkFrame(form, fg_color="transparent")
            row.pack(fill="x", pady=5)
            ctk.CTkLabel(row, text=label, width=92, anchor="w",
                         font=theme.f(12, "bold"), text_color=theme.TEXT).pack(side="left")
            ent = ctk.CTkEntry(row, width=270, height=38, font=theme.f(12),
                               show="•" if key == "password" else "")
            ent.insert(0, str(cfg.get(key, "")))
            ent.pack(side="left")
            self.conn_entries[key] = ent

        self.conn_status = ctk.CTkLabel(card, text="", font=theme.f(12),
                                        text_color=theme.DANGER)
        self.conn_status.pack(pady=(10, 0))

        ctk.CTkButton(card, text="Connect", width=350, height=46,
                      font=theme.f(15, "bold"), fg_color=theme.ACCENT,
                      hover_color=theme.ACCENT_HOVER,
                      command=self._do_connect).pack(padx=40, pady=(12, 8))
        ctk.CTkLabel(card,
                     text="Tip: start the Docker container 'my_postgres' first.",
                     font=theme.f(11), text_color=theme.SUBTEXT).pack(pady=(0, 26))

        self.bind("<Return>", lambda e: self._do_connect())
        self.after(150, lambda: self.conn_entries["password"].focus())

    def _do_connect(self):
        vals = {k: e.get().strip() for k, e in self.conn_entries.items()}
        self.conn_status.configure(text="Connecting…", text_color=theme.SUBTEXT)
        self.update_idletasks()
        try:
            self.db.connect(vals["host"], vals["port"], vals["dbname"],
                            vals["user"], vals["password"])
        except DatabaseError as e:
            self.conn_status.configure(text="✗  " + str(e).split("\n")[0],
                                       text_color=theme.DANGER)
            return
        save_config(vals)
        self.unbind("<Return>")
        self.connect_frame.destroy()
        self._build_main()

    # ===================================================================== #
    #  Main shell
    # ===================================================================== #
    def _build_main(self):
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # ---- Sidebar ----
        side = ctk.CTkFrame(self, width=240, fg_color=theme.BG_PANEL, corner_radius=0)
        side.grid(row=0, column=0, sticky="nsw")
        side.grid_propagate(False)

        ctk.CTkLabel(side, text="⚽  Fantasy League",
                     font=theme.f(20, "bold"), text_color=theme.TEXT).pack(
                     anchor="w", padx=22, pady=(26, 2))
        ctk.CTkLabel(side, text="Manager · Stage E",
                     font=theme.f(11), text_color=theme.SUBTEXT).pack(
                     anchor="w", padx=22, pady=(0, 22))

        for key, label, icon in [("dashboard", "Dashboard", "🏠"),
                                 ("tables", "Tables (CRUD)", "🗄️"),
                                 ("queries", "Queries", "🔎"),
                                 ("programs", "Programs", "⚙️")]:
            btn = ctk.CTkButton(side, text="   %s  %s" % (icon, label), anchor="w",
                                height=44, corner_radius=10, font=theme.f(14),
                                fg_color="transparent", hover_color=theme.CARD,
                                text_color=theme.TEXT,
                                command=lambda k=key: self.show(k))
            btn.pack(fill="x", padx=14, pady=3)
            self.nav_buttons[key] = btn

        bottom = ctk.CTkFrame(side, fg_color="transparent")
        bottom.pack(side="bottom", fill="x", padx=14, pady=18)
        s = self.db.settings
        ctk.CTkLabel(bottom, text="● connected", font=theme.f(11, "bold"),
                     text_color=theme.ACCENT).pack(anchor="w")
        ctk.CTkLabel(bottom, text="%s@%s/%s" % (s["user"], s["host"], s["dbname"]),
                     font=theme.f(10), text_color=theme.SUBTEXT).pack(anchor="w", pady=(0, 8))
        ctk.CTkButton(bottom, text="Disconnect", height=36, fg_color=theme.CARD,
                      hover_color=theme.DANGER_HOVER,
                      command=self._disconnect).pack(fill="x")

        # ---- Content holder ----
        self.content = ctk.CTkFrame(self, fg_color=theme.BG_DARK)
        self.content.grid(row=0, column=1, sticky="nsew")
        self.content.grid_rowconfigure(0, weight=1)
        self.content.grid_columnconfigure(0, weight=1)

        self.screens = {
            "dashboard": DashboardScreen(self.content, self),
            "tables": TablesScreen(self.content, self),
            "queries": QueriesScreen(self.content, self),
            "programs": ProgramsScreen(self.content, self),
        }
        self.show("dashboard")

    def show(self, key):
        for s in self.screens.values():
            s.grid_forget()
        self.screens[key].grid(row=0, column=0, sticky="nsew")
        for k, btn in self.nav_buttons.items():
            if k == key:
                btn.configure(fg_color=theme.ACCENT, text_color="#ffffff")
            else:
                btn.configure(fg_color="transparent", text_color=theme.TEXT)
        if hasattr(self.screens[key], "on_show"):
            self.screens[key].on_show()

    def _disconnect(self):
        if not messagebox.askyesno("Disconnect", "Close the database connection?"):
            return
        self.db.close()
        for w in self.winfo_children():
            w.destroy()
        self.nav_buttons = {}
        self._build_connect_screen()


# --------------------------------------------------------------------------- #
class BaseScreen(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color=theme.BG_DARK)
        self.app = app
        self.db = app.db


def header(parent, title, subtitle):
    box = ctk.CTkFrame(parent, fg_color="transparent")
    ctk.CTkLabel(box, text=title, font=theme.f(26, "bold"),
                 text_color=theme.TEXT).pack(anchor="w")
    ctk.CTkLabel(box, text=subtitle, font=theme.f(13),
                 text_color=theme.SUBTEXT).pack(anchor="w", pady=(2, 0))
    return box


# --------------------------------------------------------------------------- #
class DashboardScreen(BaseScreen):
    def __init__(self, master, app):
        super().__init__(master, app)
        header(self, "Dashboard", "A quick look at your fantasy universe").pack(
            anchor="w", padx=28, pady=(26, 16))

        self.cards_row = ctk.CTkFrame(self, fg_color="transparent")
        self.cards_row.pack(fill="x", padx=24)
        self.stat_cards = {}
        specs = [("Players", "⚽", theme.ACCENT), ("Clubs", "🏟️", theme.ACCENT2),
                 ("Users", "👤", "#3b82f6"), ("Fantasy Teams", "🛡️", "#f59e0b")]
        for i, (name, icon, color) in enumerate(specs):
            self.cards_row.grid_columnconfigure(i, weight=1)
            card = ctk.CTkFrame(self.cards_row, fg_color=theme.CARD, corner_radius=14,
                                height=110, border_width=1, border_color=theme.BORDER)
            card.grid(row=0, column=i, padx=8, sticky="ew")
            card.grid_propagate(False)
            ctk.CTkLabel(card, text=icon, font=theme.f(26)).pack(anchor="w", padx=18, pady=(14, 0))
            val = ctk.CTkLabel(card, text="…", font=theme.f(28, "bold"),
                               text_color=color)
            val.pack(anchor="w", padx=18)
            ctk.CTkLabel(card, text=name, font=theme.f(12), text_color=theme.SUBTEXT).pack(
                anchor="w", padx=18, pady=(0, 12))
            self.stat_cards[name] = val

        ctk.CTkLabel(self, text="Top 10 Scorers", font=theme.f(18, "bold"),
                     text_color=theme.TEXT).pack(anchor="w", padx=28, pady=(22, 8))
        self.grid_view = DataGrid(self)
        self.grid_view.pack(fill="both", expand=True, padx=24, pady=(0, 24))
        self._loaded = False

    def on_show(self):
        if self._loaded:
            return
        self._loaded = True
        self.refresh()

    def refresh(self):
        counts = {
            "Players": "SELECT COUNT(*) FROM player",
            "Clubs": "SELECT COUNT(*) FROM real_team",
            "Users": "SELECT COUNT(*) FROM users",
            "Fantasy Teams": "SELECT COUNT(*) FROM fantasy_team",
        }
        for name, sql in counts.items():
            try:
                self.stat_cards[name].configure(text=str(self.db.scalar(sql)))
            except DatabaseError:
                self.stat_cards[name].configure(text="—")
        try:
            cols, rows = self.db.fetch("""
                SELECT p.first_name || ' ' || p.last_name AS "Player",
                       (SELECT team_name FROM real_team r WHERE r.real_team_id = p.real_team_id) AS "Club",
                       (SELECT position_name FROM position pos WHERE pos.position_id = p.position_id) AS "Position",
                       p.price AS "Price (£m)",
                       p.total_points AS "Points"
                FROM   player p
                ORDER  BY p.total_points DESC
                LIMIT  10
            """)
            self.grid_view.set_data(cols, rows)
        except DatabaseError as e:
            messagebox.showerror("Database error", str(e))


# --------------------------------------------------------------------------- #
class TablesScreen(BaseScreen):
    def __init__(self, master, app):
        super().__init__(master, app)
        self.current = md.TABLE_ORDER[0]
        self.headers = []
        self.pk_indices = []

        header(self, "Tables", "Create, read, update and delete - foreign keys shown by name").pack(
            anchor="w", padx=28, pady=(26, 14))

        # ---- toolbar ----
        bar = ctk.CTkFrame(self, fg_color="transparent")
        bar.pack(fill="x", padx=24)

        self.table_map = {}
        options = []
        for key in md.TABLE_ORDER:
            m = md.TABLES[key]
            disp = "%s  %s" % (m["icon"], m["title"])
            self.table_map[disp] = key
            options.append(disp)
        self.table_menu = ctk.CTkOptionMenu(
            bar, values=options, width=240, height=40, font=theme.f(13),
            fg_color=theme.CARD, button_color=theme.ACCENT,
            button_hover_color=theme.ACCENT_HOVER, command=self._on_table_change)
        self.table_menu.pack(side="left")

        self.search = ctk.CTkEntry(bar, placeholder_text="Search this table…",
                                   width=240, height=40, font=theme.f(12))
        self.search.pack(side="left", padx=10)
        self.search.bind("<Return>", lambda e: self.load())

        ctk.CTkButton(bar, text="Search", width=80, height=40, fg_color=theme.CARD,
                      hover_color=theme.CARD_HOVER, command=self.load).pack(side="left")
        ctk.CTkButton(bar, text="↻", width=44, height=40, fg_color=theme.CARD,
                      hover_color=theme.CARD_HOVER, command=self.load).pack(side="left", padx=(8, 0))

        ctk.CTkButton(bar, text="🗑 Delete", width=100, height=40, fg_color=theme.CARD,
                      hover_color=theme.DANGER_HOVER, command=self.delete_row).pack(side="right")
        ctk.CTkButton(bar, text="✎ Edit", width=90, height=40, fg_color=theme.ACCENT2,
                      hover_color=theme.ACCENT2_HOVER, command=self.edit_row).pack(side="right", padx=8)
        ctk.CTkButton(bar, text="＋ Add", width=90, height=40, fg_color=theme.ACCENT,
                      hover_color=theme.ACCENT_HOVER, command=self.add_row).pack(side="right")

        self.grid_view = DataGrid(self, on_double_click=self.edit_row)
        self.grid_view.pack(fill="both", expand=True, padx=24, pady=14)

        self.status = ctk.CTkLabel(self, text="", font=theme.f(12),
                                   text_color=theme.SUBTEXT)
        self.status.pack(anchor="w", padx=28, pady=(0, 16))
        self._loaded = False

    def on_show(self):
        if not self._loaded:
            self._loaded = True
            self.table_menu.set(self._disp_for(self.current))
            self.load()

    def _disp_for(self, key):
        m = md.TABLES[key]
        return "%s  %s" % (m["icon"], m["title"])

    def _on_table_change(self, disp):
        self.current = self.table_map[disp]
        self.search.delete(0, "end")
        self.load()

    def load(self):
        term = self.search.get().strip() or None
        try:
            sql, params, headers = md.build_browse_sql(self.current, term)
            cols, rows = self.db.fetch(sql, params)
        except DatabaseError as e:
            messagebox.showerror("Database error", str(e))
            return
        self.headers = cols
        # find which displayed columns are the primary key (shown raw)
        meta = md.TABLES[self.current]
        pk_labels = []
        for p in meta["pk"]:
            col = next(c for c in meta["columns"] if c["name"] == p)
            pk_labels.append(col["label"])
        self.pk_indices = [cols.index(lbl) for lbl in pk_labels if lbl in cols]
        self.grid_view.set_data(cols, rows)
        extra = "  (showing first 500)" if len(rows) >= 500 else ""
        self.status.configure(text="%d row(s)%s · %s" % (len(rows), extra, meta["title"]))

    def _selected_pk(self):
        row = self.grid_view.selected_row()
        if not row:
            messagebox.showinfo("Select a row", "Please select a row in the grid first.")
            return None
        return [row[i] for i in self.pk_indices]

    def add_row(self):
        RecordForm(self, self.db, self.current, "insert", on_saved=self.load)

    def edit_row(self):
        pk = self._selected_pk()
        if pk is None:
            return
        RecordForm(self, self.db, self.current, "update", pk_values=pk, on_saved=self.load)

    def delete_row(self):
        pk = self._selected_pk()
        if pk is None:
            return
        meta = md.TABLES[self.current]
        if not messagebox.askyesno(
                "Confirm delete",
                "Delete this row from %s?\nKey: %s\n\nThis cannot be undone."
                % (meta["title"], ", ".join(map(str, pk)))):
            return
        where = " AND ".join("%s = %%s" % p for p in meta["pk"])
        sql = "DELETE FROM %s WHERE %s" % (self.current, where)
        try:
            count, _ = self.db.execute(sql, pk)
        except DatabaseError as e:
            messagebox.showerror("Could not delete",
                                 str(e) + "\n\n(The row may be referenced by other tables.)")
            return
        messagebox.showinfo("Deleted", "Removed %d row(s)." % count)
        self.load()


# --------------------------------------------------------------------------- #
def build_param_inputs(parent, params):
    """Create labelled entries for a list of param specs. Returns a reader fn."""
    entries = {}
    for p in params:
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", pady=5)
        ctk.CTkLabel(row, text=p["label"], width=140, anchor="w",
                     font=theme.f(12, "bold"), text_color=theme.TEXT).pack(side="left")
        ent = ctk.CTkEntry(row, width=200, height=36, font=theme.f(12))
        ent.insert(0, str(p.get("default", "")))
        ent.pack(side="left")
        entries[p["name"]] = (ent, p["type"])

    def read():
        out = []
        for p in params:
            ent, typ = entries[p["name"]]
            raw = ent.get().strip()
            if typ == "int":
                if raw == "":
                    raise ValueError("'%s' must be a number." % p["label"])
                try:
                    out.append(int(raw))
                except ValueError:
                    raise ValueError("'%s' must be a whole number." % p["label"])
            else:
                out.append(raw)
        return out
    return read


class QueriesScreen(BaseScreen):
    def __init__(self, master, app):
        super().__init__(master, app)
        header(self, "Queries", "Stage B queries running on the integrated database").pack(
            anchor="w", padx=28, pady=(26, 14))

        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=24, pady=(0, 20))
        body.grid_rowconfigure(0, weight=1)
        body.grid_columnconfigure(1, weight=1)

        # left: list of queries
        left = ctk.CTkScrollableFrame(body, width=290, fg_color=theme.BG_PANEL,
                                      corner_radius=12, label_text="Select a query")
        left.grid(row=0, column=0, sticky="ns", padx=(0, 16))
        self.query_buttons = {}
        for q in progs.QUERIES:
            b = ctk.CTkButton(left, text=q["title"], anchor="w", height=46,
                              font=theme.f(13), fg_color=theme.CARD,
                              hover_color=theme.CARD_HOVER, text_color=theme.TEXT,
                              command=lambda x=q: self.select(x))
            b.pack(fill="x", pady=5, padx=4)
            self.query_buttons[q["id"]] = b

        # right: detail + results
        right = ctk.CTkFrame(body, fg_color="transparent")
        right.grid(row=0, column=1, sticky="nsew")
        right.grid_rowconfigure(2, weight=1)
        right.grid_columnconfigure(0, weight=1)

        self.detail = ctk.CTkFrame(right, fg_color=theme.CARD, corner_radius=12)
        self.detail.grid(row=0, column=0, sticky="ew")
        self.q_title = ctk.CTkLabel(self.detail, text="Pick a query on the left",
                                    font=theme.f(18, "bold"), text_color=theme.TEXT)
        self.q_title.pack(anchor="w", padx=18, pady=(16, 2))
        self.q_desc = ctk.CTkLabel(self.detail, text="", font=theme.f(12),
                                   text_color=theme.SUBTEXT, justify="left", wraplength=560)
        self.q_desc.pack(anchor="w", padx=18, pady=(0, 8))
        self.param_box = ctk.CTkFrame(self.detail, fg_color="transparent")
        self.param_box.pack(fill="x", padx=18, pady=(0, 6))
        self.run_btn = ctk.CTkButton(self.detail, text="▶  Run query", height=40,
                                     font=theme.f(13, "bold"), fg_color=theme.ACCENT,
                                     hover_color=theme.ACCENT_HOVER, state="disabled",
                                     command=self.run)
        self.run_btn.pack(anchor="w", padx=18, pady=(2, 16))

        self.status = ctk.CTkLabel(right, text="", font=theme.f(12),
                                   text_color=theme.SUBTEXT)
        self.status.grid(row=1, column=0, sticky="w", pady=6)

        self.grid_view = DataGrid(right)
        self.grid_view.grid(row=2, column=0, sticky="nsew")

        self.current = None
        self.read_params = lambda: []

    def select(self, q):
        self.current = q
        for qid, b in self.query_buttons.items():
            b.configure(fg_color=theme.ACCENT if qid == q["id"] else theme.CARD,
                        text_color="#ffffff" if qid == q["id"] else theme.TEXT)
        self.q_title.configure(text=q["title"])
        self.q_desc.configure(text=q["desc"])
        for w in self.param_box.winfo_children():
            w.destroy()
        self.read_params = build_param_inputs(self.param_box, q["params"])
        self.run_btn.configure(state="normal")
        self.grid_view.clear()
        self.status.configure(text="")

    def run(self):
        if not self.current:
            return
        try:
            params = self.read_params()
        except ValueError as e:
            messagebox.showwarning("Check parameters", str(e))
            return
        try:
            cols, rows = self.db.fetch(self.current["sql"], params)
        except DatabaseError as e:
            messagebox.showerror("Query failed", str(e))
            return
        self.grid_view.set_data(cols, rows)
        self.status.configure(text="✓  %d row(s) returned" % len(rows),
                              text_color=theme.ACCENT)


# --------------------------------------------------------------------------- #
class ProgramsScreen(BaseScreen):
    def __init__(self, master, app):
        super().__init__(master, app)
        header(self, "Programs", "Stage D PL/pgSQL functions & procedures").pack(
            anchor="w", padx=28, pady=(26, 14))

        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=24, pady=(0, 20))
        body.grid_rowconfigure(0, weight=1)
        body.grid_columnconfigure(1, weight=1)

        left = ctk.CTkScrollableFrame(body, width=290, fg_color=theme.BG_PANEL,
                                      corner_radius=12, label_text="Select a program")
        left.grid(row=0, column=0, sticky="ns", padx=(0, 16))
        self.prog_buttons = {}
        for p in progs.PROGRAMS:
            tag = "ƒ  function" if p["kind"] != "procedure" else "▣  procedure"
            short = p["title"].split(": ", 1)[-1]
            b = ctk.CTkButton(left, text="%s  %s\n     %s" % (p["icon"], short, tag),
                              anchor="w", height=58, font=theme.f(12),
                              fg_color=theme.CARD, hover_color=theme.CARD_HOVER,
                              text_color=theme.TEXT, command=lambda x=p: self.select(x))
            b.pack(fill="x", pady=5, padx=4)
            self.prog_buttons[p["id"]] = b

        right = ctk.CTkFrame(body, fg_color="transparent")
        right.grid(row=0, column=1, sticky="nsew")
        right.grid_rowconfigure(3, weight=1)
        right.grid_columnconfigure(0, weight=1)

        self.detail = ctk.CTkFrame(right, fg_color=theme.CARD, corner_radius=12)
        self.detail.grid(row=0, column=0, sticky="ew")
        self.p_title = ctk.CTkLabel(self.detail, text="Pick a program on the left",
                                    font=theme.f(18, "bold"), text_color=theme.TEXT)
        self.p_title.pack(anchor="w", padx=18, pady=(16, 2))
        self.p_desc = ctk.CTkLabel(self.detail, text="", font=theme.f(12),
                                   text_color=theme.SUBTEXT, justify="left", wraplength=560)
        self.p_desc.pack(anchor="w", padx=18, pady=(0, 8))
        self.param_box = ctk.CTkFrame(self.detail, fg_color="transparent")
        self.param_box.pack(fill="x", padx=18, pady=(0, 6))
        self.run_btn = ctk.CTkButton(self.detail, text="▶  Run program", height=40,
                                     font=theme.f(13, "bold"), fg_color=theme.ACCENT,
                                     hover_color=theme.ACCENT_HOVER, state="disabled",
                                     command=self.run)
        self.run_btn.pack(anchor="w", padx=18, pady=(2, 16))

        # NOTICE / message log
        ctk.CTkLabel(right, text="Output log", font=theme.f(12, "bold"),
                     text_color=theme.SUBTEXT).grid(row=1, column=0, sticky="w", pady=(8, 2))
        self.log = ctk.CTkTextbox(right, height=120, font=("Consolas", 11),
                                  fg_color=theme.BG_PANEL, text_color=theme.TEXT)
        self.log.grid(row=2, column=0, sticky="ew")
        self.log.configure(state="disabled")

        self.grid_view = DataGrid(right)
        self.grid_view.grid(row=3, column=0, sticky="nsew", pady=(10, 0))

        self.current = None
        self.read_params = lambda: []

    def select(self, p):
        self.current = p
        for pid, b in self.prog_buttons.items():
            b.configure(fg_color=theme.ACCENT if pid == p["id"] else theme.CARD,
                        text_color="#ffffff" if pid == p["id"] else theme.TEXT)
        self.p_title.configure(text=p["title"])
        self.p_desc.configure(text=p["desc"])
        for w in self.param_box.winfo_children():
            w.destroy()
        self.read_params = build_param_inputs(self.param_box, p["params"])
        self.run_btn.configure(state="normal")
        self.grid_view.clear()
        self._set_log("")

    def _set_log(self, text):
        self.log.configure(state="normal")
        self.log.delete("1.0", "end")
        self.log.insert("1.0", text)
        self.log.configure(state="disabled")

    def run(self):
        if not self.current:
            return
        try:
            params = self.read_params()
        except ValueError as e:
            messagebox.showwarning("Check parameters", str(e))
            return
        p = self.current
        try:
            if p["kind"] == "function_table":
                cols, rows = self.db.call_function_table(p["sql"], params)
                self.grid_view.set_data(cols, rows)
                self._set_log("Function %s returned %d row(s)." % (p["fn"], len(rows)))
            elif p["kind"] == "refcursor":
                cols, rows, notices = self.db.call_refcursor(
                    p["sql"], p["cursor_name"], params)
                self.grid_view.set_data(cols, rows)
                self._set_log(self._fmt_notices(notices)
                              + "\nCursor returned %d row(s)." % len(rows))
            elif p["kind"] == "procedure":
                notices = self.db.call_procedure(p["call"], params)
                log = self._fmt_notices(notices) or "Procedure completed."
                self._set_log(log)
                if p.get("post_sql"):
                    post_params = params if "%s" in p["post_sql"] else None
                    cols, rows = self.db.fetch(p["post_sql"], post_params)
                    self.grid_view.set_data(cols, rows)
        except DatabaseError as e:
            self._set_log("✗  " + str(e))
            messagebox.showerror("Program failed", str(e))

    @staticmethod
    def _fmt_notices(notices):
        if not notices:
            return ""
        return "\n".join("• " + n.replace("NOTICE:  ", "").strip()
                         for n in notices[-200:])


# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    App().mainloop()
