"""
widgets.py - Reusable UI building blocks:

  DataGrid   : a styled ttk.Treeview with scrollbars + zebra rows.
  FKPicker   : a modal search dialog to choose a foreign-key value by NAME.
  RecordForm : a modal add/edit form generated from a table's metadata.
"""
import tkinter as tk
from tkinter import ttk, messagebox
import customtkinter as ctk

import theme
import metadata as md
from db import DatabaseError


# --------------------------------------------------------------------------- #
class DataGrid(ctk.CTkFrame):
    """A scrollable, zebra-striped results grid."""

    def __init__(self, master, on_double_click=None, **kw):
        super().__init__(master, fg_color=theme.GRID_ODD, corner_radius=10, **kw)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.tree = ttk.Treeview(self, style="Fantasy.Treeview", show="headings",
                                 selectmode="browse")
        self.tree.grid(row=0, column=0, sticky="nsew", padx=2, pady=2)

        vsb = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(self, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")

        self.tree.tag_configure("even", background=theme.GRID_EVEN)
        self.tree.tag_configure("odd", background=theme.GRID_ODD)

        if on_double_click:
            self.tree.bind("<Double-1>", lambda e: on_double_click())

    def set_data(self, headers, rows):
        self.tree.delete(*self.tree.get_children())
        self.tree["columns"] = headers
        sample = rows[:80]
        for ci, h in enumerate(headers):
            self.tree.heading(h, text=h)
            # size each column from the widest of its header / sampled values
            longest = len(str(h))
            for r in sample:
                if ci < len(r) and r[ci] is not None:
                    longest = max(longest, len(str(r[ci])))
            width = max(80, min(440, 16 + longest * 9))
            self.tree.column(h, width=width, anchor="w", stretch=False)
        for i, row in enumerate(rows):
            vals = ["" if v is None else str(v) for v in row]
            self.tree.insert("", "end", values=vals,
                             tags=("even" if i % 2 == 0 else "odd",))

    def selected_row(self):
        sel = self.tree.selection()
        if not sel:
            return None
        return self.tree.item(sel[0], "values")

    def clear(self):
        self.tree.delete(*self.tree.get_children())
        self.tree["columns"] = ()


# --------------------------------------------------------------------------- #
class FKPicker(ctk.CTkToplevel):
    """Modal dialog: search a referenced table and return the chosen (id, label)."""

    def __init__(self, master, db, table, title=None):
        super().__init__(master)
        self.db = db
        self.table = table
        self.result = None  # (id, label) or None

        self.title("Choose %s" % (title or md.TABLES[table]["title"]))
        self.configure(fg_color=theme.BG_DARK)
        self.geometry("520x560")
        self.transient(master)
        self.grab_set()

        ctk.CTkLabel(self, text="Search %s" % md.TABLES[table]["title"],
                     font=theme.f(18, "bold"), text_color=theme.TEXT).pack(
                     anchor="w", padx=20, pady=(18, 6))

        self.search = ctk.CTkEntry(self, placeholder_text="Type to filter by name…",
                                   height=38, font=theme.f(12))
        self.search.pack(fill="x", padx=20)
        self.search.bind("<KeyRelease>", lambda e: self._refresh())

        grid_holder = ctk.CTkFrame(self, fg_color=theme.GRID_ODD, corner_radius=10)
        grid_holder.pack(fill="both", expand=True, padx=20, pady=12)
        grid_holder.grid_rowconfigure(0, weight=1)
        grid_holder.grid_columnconfigure(0, weight=1)

        self.tree = ttk.Treeview(grid_holder, style="Fantasy.Treeview", show="headings",
                                 columns=("id", "label"), selectmode="browse")
        self.tree.heading("id", text="ID")
        self.tree.heading("label", text="Name")
        self.tree.column("id", width=90, anchor="w", stretch=False)
        self.tree.column("label", width=360, anchor="w")
        self.tree.tag_configure("even", background=theme.GRID_EVEN)
        self.tree.tag_configure("odd", background=theme.GRID_ODD)
        self.tree.grid(row=0, column=0, sticky="nsew", padx=2, pady=2)
        vsb = ttk.Scrollbar(grid_holder, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        vsb.grid(row=0, column=1, sticky="ns")
        self.tree.bind("<Double-1>", lambda e: self._choose())

        btns = ctk.CTkFrame(self, fg_color="transparent")
        btns.pack(fill="x", padx=20, pady=(0, 16))
        ctk.CTkButton(btns, text="Clear (set empty)", width=130, height=38,
                      fg_color=theme.CARD, hover_color=theme.CARD_HOVER,
                      command=self._clear).pack(side="left")
        ctk.CTkButton(btns, text="Cancel", width=100, height=38,
                      fg_color=theme.CARD, hover_color=theme.CARD_HOVER,
                      command=self.destroy).pack(side="right", padx=(8, 0))
        ctk.CTkButton(btns, text="Select", width=120, height=38,
                      fg_color=theme.ACCENT, hover_color=theme.ACCENT_HOVER,
                      command=self._choose).pack(side="right")

        self._refresh()
        self.after(120, self.search.focus)

    def _refresh(self):
        term = self.search.get().strip() or None
        try:
            sql, params = md.fk_options_sql(self.table, term)
            _, rows = self.db.fetch(sql, params)
        except DatabaseError as e:
            messagebox.showerror("Database error", str(e), parent=self)
            return
        self.tree.delete(*self.tree.get_children())
        for i, (rid, label) in enumerate(rows):
            self.tree.insert("", "end", values=(rid, label),
                             tags=("even" if i % 2 == 0 else "odd",))

    def _choose(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Pick one", "Please select a row first.", parent=self)
            return
        rid, label = self.tree.item(sel[0], "values")
        self.result = (rid, label)
        self.destroy()

    def _clear(self):
        self.result = ("", "")  # explicit empty selection
        self.destroy()


# --------------------------------------------------------------------------- #
class RecordForm(ctk.CTkToplevel):
    """Modal Add / Edit form generated from table metadata."""

    def __init__(self, master, db, table, mode, pk_values=None, on_saved=None):
        super().__init__(master)
        self.db = db
        self.table = table
        self.mode = mode                 # "insert" | "update"
        self.pk_values = pk_values
        self.on_saved = on_saved
        self.meta = md.TABLES[table]
        self.widgets = {}                # column name -> widget / holder
        self.fk_values = {}              # column name -> current id (str)

        verb = "Add new" if mode == "insert" else "Edit"
        self.title("%s - %s" % (verb, self.meta["title"]))
        self.configure(fg_color=theme.BG_DARK)
        self.geometry("520x680")
        self.transient(master)
        self.grab_set()

        ctk.CTkLabel(self, text="%s  %s %s" % (self.meta["icon"], verb, self.meta["title"]),
                     font=theme.f(20, "bold"), text_color=theme.TEXT).pack(
                     anchor="w", padx=24, pady=(20, 2))
        ctk.CTkLabel(self,
                     text=("Foreign keys are chosen by name." if mode == "insert"
                           else "Primary key is fixed; other fields were loaded for editing."),
                     font=theme.f(11), text_color=theme.SUBTEXT).pack(anchor="w", padx=24)

        self.body = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.body.pack(fill="both", expand=True, padx=14, pady=12)

        self.cols = md.editable_columns(table, mode)
        self._build_fields()

        if mode == "update":
            self._load_existing()
        else:
            self._suggest_pk()

        btns = ctk.CTkFrame(self, fg_color="transparent")
        btns.pack(fill="x", padx=24, pady=(0, 18))
        ctk.CTkButton(btns, text="Cancel", width=110, height=42,
                      fg_color=theme.CARD, hover_color=theme.CARD_HOVER,
                      command=self.destroy).pack(side="right", padx=(8, 0))
        ctk.CTkButton(btns, text="Save", width=150, height=42, font=theme.f(13, "bold"),
                      fg_color=theme.ACCENT, hover_color=theme.ACCENT_HOVER,
                      command=self._save).pack(side="right")

    # ----------------------------------------------------------- build fields
    def _build_fields(self):
        for col in self.cols:
            row = ctk.CTkFrame(self.body, fg_color="transparent")
            row.pack(fill="x", pady=6, padx=6)
            req = "" if col.get("locked") else ""
            ctk.CTkLabel(row, text=col["label"] + req, width=150, anchor="w",
                         font=theme.f(12, "bold"), text_color=theme.TEXT).pack(
                         side="left", padx=(0, 8))

            if col.get("fk") and not col.get("pk_is_fk"):
                self._build_fk_field(row, col)
            elif col.get("fk") and col.get("pk_is_fk") and self.mode == "insert":
                # PK that is also a FK (referee/intl_player) - pick the person.
                self._build_fk_field(row, col)
            elif col["type"] == "bool":
                self._build_bool_field(row, col)
            else:
                self._build_text_field(row, col)

    def _build_text_field(self, row, col):
        ph = ""
        if col["type"] == "date":
            ph = "YYYY-MM-DD"
        elif col["type"] == "time":
            ph = "HH:MM:SS"
        elif col["type"] in ("int", "num"):
            ph = "number"
        ent = ctk.CTkEntry(row, height=36, font=theme.f(12), placeholder_text=ph)
        ent.pack(side="left", fill="x", expand=True)
        if col.get("locked"):
            ent.configure(state="disabled")
        self.widgets[col["name"]] = ("text", ent)

    def _build_bool_field(self, row, col):
        var = tk.IntVar(value=0)
        sw = ctk.CTkSwitch(row, text="", variable=var,
                           progress_color=theme.ACCENT)
        sw.pack(side="left")
        self.widgets[col["name"]] = ("bool", var)

    def _build_fk_field(self, row, col):
        holder = ctk.CTkFrame(row, fg_color="transparent")
        holder.pack(side="left", fill="x", expand=True)
        lbl = ctk.CTkButton(
            holder, text="— choose —", anchor="w", height=36,
            fg_color=theme.CARD, hover_color=theme.CARD_HOVER, text_color=theme.SUBTEXT,
            command=lambda c=col: self._open_fk_picker(c))
        lbl.pack(side="left", fill="x", expand=True)
        if col.get("locked"):
            lbl.configure(state="disabled")
        self.widgets[col["name"]] = ("fk", lbl)
        self.fk_values[col["name"]] = ""

    def _open_fk_picker(self, col):
        picker = FKPicker(self, self.db, col["fk"], title=col["label"])
        self.wait_window(picker)
        if picker.result is None:
            return
        rid, label = picker.result
        self.fk_values[col["name"]] = rid
        btn = self.widgets[col["name"]][1]
        if rid == "":
            btn.configure(text="— none —", text_color=theme.SUBTEXT)
        else:
            btn.configure(text="%s  (#%s)" % (label, rid), text_color=theme.TEXT)

    # --------------------------------------------------------------- prefill
    def _suggest_pk(self):
        """For a single integer PK, suggest the next id."""
        if len(self.meta["pk"]) != 1:
            return
        pk = self.meta["pk"][0]
        pkcol = next((c for c in self.meta["columns"] if c["name"] == pk), None)
        if not pkcol or pkcol["type"] != "int":
            return
        try:
            nxt = self.db.scalar("SELECT COALESCE(MAX(%s),0)+1 FROM %s" % (pk, self.table))
        except DatabaseError:
            return
        kind, w = self.widgets.get(pk, (None, None))
        if kind == "text" and nxt is not None:
            w.insert(0, str(nxt))

    def _load_existing(self):
        sql, cols = md.build_select_row_sql(self.table)
        try:
            _, row = self.db.fetch_one(sql, self.pk_values)
        except DatabaseError as e:
            messagebox.showerror("Database error", str(e), parent=self)
            self.destroy()
            return
        if row is None:
            messagebox.showerror("Not found", "No row matches that key.", parent=self)
            self.destroy()
            return
        data = dict(zip(cols, row))
        for col in self.cols:
            name = col["name"]
            val = data.get(name)
            kind, w = self.widgets[name]
            if kind == "text":
                state = w.cget("state")
                if state == "disabled":
                    w.configure(state="normal")
                w.delete(0, "end")
                if val is not None:
                    w.insert(0, str(val))
                if col.get("locked"):
                    w.configure(state="disabled")
            elif kind == "bool":
                w.set(1 if val in (1, True, "1") else 0)
            elif kind == "fk":
                if val is None or val == "":
                    w.configure(text="— none —", text_color=theme.SUBTEXT)
                    self.fk_values[name] = ""
                else:
                    self.fk_values[name] = str(val)
                    label = self._fk_label(col["fk"], val)
                    w.configure(text="%s  (#%s)" % (label, val), text_color=theme.TEXT)

    def _fk_label(self, table, value):
        try:
            return self.db.scalar(md.label_for_id(table), (value,)) or str(value)
        except DatabaseError:
            return str(value)

    # ----------------------------------------------------------------- save
    def _collect(self):
        """Return {column: value} with empty strings turned into None."""
        out = {}
        for col in self.cols:
            name = col["name"]
            kind, w = self.widgets[name]
            if kind == "text":
                if w.cget("state") == "disabled":
                    # locked PK in update mode - read its shown value
                    raw = w.get()
                else:
                    raw = w.get().strip()
                out[name] = raw if raw != "" else None
            elif kind == "bool":
                out[name] = w.get()
            elif kind == "fk":
                rid = self.fk_values.get(name, "")
                out[name] = rid if rid != "" else None
        return out

    def _save(self):
        values = self._collect()

        # Basic required check: non-nullable-ish key fields must be present.
        for col in self.cols:
            if col["name"] in self.meta["pk"] and not col.get("locked"):
                if values.get(col["name"]) in (None, ""):
                    messagebox.showwarning("Missing key",
                                           "Primary key '%s' is required." % col["label"],
                                           parent=self)
                    return

        try:
            if self.mode == "insert":
                self._do_insert(values)
            else:
                self._do_update(values)
        except DatabaseError as e:
            messagebox.showerror("Could not save", str(e), parent=self)
            return

        if self.on_saved:
            self.on_saved()
        self.destroy()

    def _do_insert(self, values):
        cols = [c["name"] for c in self.cols]
        placeholders = ", ".join(["%s"] * len(cols))
        sql = "INSERT INTO %s (%s) VALUES (%s)" % (
            self.table, ", ".join(cols), placeholders)
        params = [values[c] for c in cols]
        self.db.execute(sql, params)
        messagebox.showinfo("Saved", "New row added successfully.", parent=self.master)

    def _do_update(self, values):
        set_cols = [c["name"] for c in self.cols if not c.get("locked")]
        set_sql = ", ".join("%s = %%s" % c for c in set_cols)
        where = " AND ".join("%s = %%s" % p for p in self.meta["pk"])
        sql = "UPDATE %s SET %s WHERE %s" % (self.table, set_sql, where)
        params = [values[c] for c in set_cols] + list(self.pk_values)
        count, _ = self.db.execute(sql, params)
        messagebox.showinfo("Saved", "Updated %d row(s)." % count, parent=self.master)
