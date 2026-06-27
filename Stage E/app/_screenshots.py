"""
_screenshots.py - Drives the GUI automatically and saves PNG screenshots of
every screen into ../screenshots. Helper used to produce images for the report.
Run:  python _screenshots.py
"""
import os
import time
import tkinter as tk
from PIL import ImageGrab

import app as A
import programs as progs
from widgets import RecordForm, FKPicker

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "screenshots")
os.makedirs(OUT, exist_ok=True)

CONN = dict(host="localhost", port="5432", dbname="mydatabase",
            user="myuser", password="mypassword")


def settle(win, n=8, dt=0.06):
    for _ in range(n):
        win.update_idletasks()
        win.update()
        time.sleep(dt)


def grab(win, name):
    win.deiconify()
    win.lift()
    win.focus_force()
    settle(win, 10, 0.05)
    x, y = win.winfo_rootx(), win.winfo_rooty()
    w, h = win.winfo_width(), win.winfo_height()
    img = ImageGrab.grab(bbox=(x, y, x + w, y + h))
    path = os.path.join(OUT, name)
    img.save(path)
    print("saved", name, img.size)


def main():
    app = A.App()
    app.geometry("1200x760+60+30")
    settle(app)

    # 1) Connection screen
    grab(app, "01_connection.png")

    # connect
    for k, v in CONN.items():
        app.conn_entries[k].delete(0, "end")
        app.conn_entries[k].insert(0, v)
    app._do_connect()
    settle(app, 12)

    # 2) Dashboard
    app.show("dashboard")
    app.screens["dashboard"].refresh()
    settle(app, 12)
    grab(app, "02_dashboard.png")

    # 3) Tables - players (FK names resolved)
    app.show("tables")
    ts = app.screens["tables"]
    ts._loaded = True
    ts.current = "player"
    ts.table_menu.set(ts._disp_for("player"))
    ts.load()
    settle(app, 10)
    grab(app, "03_tables_players.png")

    # 3b) Tables - matches (two FK clubs + status resolved)
    ts.current = "match"
    ts.table_menu.set(ts._disp_for("match"))
    ts.load()
    settle(app, 10)
    grab(app, "03b_tables_matches.png")

    # 4) Add form (insert) for player
    form = RecordForm(ts, app.db, "player", "insert")
    form.geometry("520x680+700+60")
    settle(form, 12)
    grab(form, "04_add_form.png")

    # 5) FK picker (choose a club)
    picker = FKPicker(form, app.db, "real_team", title="Club")
    picker.geometry("520x560+740+90")
    picker.search.insert(0, "man")
    picker._refresh()
    settle(picker, 12)
    grab(picker, "05_fk_picker.png")
    picker.destroy()
    form.destroy()
    settle(app, 4)

    # 6) Queries - run one with results
    app.show("queries")
    qs = app.screens["queries"]
    q = next(x for x in progs.QUERIES if x["id"] == "q1")
    qs.select(q)
    qs.run()
    settle(app, 10)
    grab(app, "06_queries.png")

    # 7) Programs - run the team-evaluation function
    app.show("programs")
    ps = app.screens["programs"]
    p = next(x for x in progs.PROGRAMS if x["id"] == "fn_eval")
    ps.select(p)
    ps.run()
    settle(app, 10)
    grab(app, "07_programs_function.png")

    # 7b) Programs - run a procedure (price update) showing NOTICE log + grid
    p2 = next(x for x in progs.PROGRAMS if x["id"] == "pr_prices")
    ps.select(p2)
    ps.run()
    settle(app, 12)
    grab(app, "07b_programs_procedure.png")

    app.destroy()
    print("DONE - screenshots in", os.path.abspath(OUT))


if __name__ == "__main__":
    main()
