# ==== ACME Inc. portfolio ===============================================
# Project: create_read_update_delete_simple_io_data_base | File: main.py
# About: ACME CRUD Hub — the desktop window over the shared database: one tab per table...
# Copyright (c) 2026 kjFriday | SPDX-License-Identifier: AGPL-3.0-only
# You may change this file under the AGPL-3.0. The stamp at the end marks
# the version kjFriday wrote. Verify with the portfolio's stamp.py --check.
# Reused code, if any, is mapped in PROVENANCE.md.
# ========================================================================

"""ACME CRUD Hub — the desktop window over the shared database: one tab per table, Add/Update/Delete/Clear.

    python main.py [--db PATH]          open the window
    python main.py --install            install for this user (Start menu, Apps & features)
    python main.py --uninstall          remove it again; the database stays
The hub owns the schema and creates the database; File > Seed demo data fills it (after a backup).
"""

import argparse
import ctypes
import json
import os
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from tkinter import font as tkfont

import db
import installer
import paths
import seed
from version import APP_ID, CREDIT, NAME, PUBLISHER, TITLE, __version__

HERE = os.path.dirname(os.path.abspath(__file__))
ICON = os.path.join(HERE, "icon", "app.ico")
ICON_PNG = os.path.join(HERE, "icon", "app-32.png")
# what an install copies: the program, its data files and icon (tests and tools stay behind)
RUNTIME = ["main.py", "db.py", "paths.py", "seed.py", "lorem.py", "textsafe.py", "installer.py", "version.py",
           "data", "icon"]


class TablePage(ttk.Frame):
    def __init__(self, parent, table):
        super().__init__(parent)
        self.table = table
        self.cols = db.columns(table)

        # Form Frame
        form = ttk.LabelFrame(self, text=f" {table.title()} Details ")
        form.pack(fill="x", padx=10, pady=10)
        self.entries = {}
        for i, col in enumerate(self.cols):
            ttk.Label(form, text=col.replace("_", " ").title() + ":").grid(row=i // 2, column=(i % 2) * 2, padx=5, pady=3, sticky="w")
            entry = ttk.Entry(form)
            entry.grid(row=i // 2, column=(i % 2) * 2 + 1, padx=5, pady=3, sticky="ew")
            self.entries[col] = entry
        form.columnconfigure(1, weight=1)
        form.columnconfigure(3, weight=1)

        # Button Frame
        buttons = ttk.Frame(self)
        buttons.pack(fill="x", padx=10, pady=5)
        for text, cmd in [("Add", self.create_record), ("Update", self.update_record),
                          ("Delete", self.delete_record), ("Clear", self.clear_entries),
                          ("Refresh", self.populate_tree)]:
            ttk.Button(buttons, text=text, command=cmd).pack(side="left", padx=5)

        # Treeview Frame (Data Table)
        frame_tree = ttk.Frame(self)
        frame_tree.pack(fill="both", expand=True, padx=10, pady=10)
        self.tree = ttk.Treeview(frame_tree, columns=["id"] + self.cols, show="headings")
        self.tree.heading("id", text="ID")
        self.tree.column("id", width=50, anchor="center")
        for col in self.cols:
            self.tree.heading(col, text=col.replace("_", " ").title())
            self.tree.column(col, width=120)
        scrollbar = ttk.Scrollbar(frame_tree, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        self.tree.bind("<<TreeviewSelect>>", self.select_record)

        self.populate_tree()

    def form_data(self):
        return {c: e.get() for c, e in self.entries.items() if e.get() != ""}

    def selected_id(self, action):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Selection Error", f"Please select a record to {action}.")
            return None
        return self.tree.item(selected[0])["values"][0]

    def populate_tree(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        for row in db.list_rows(self.table):
            self.tree.insert("", "end", values=[row["id"]] + ["" if row[c] is None else row[c] for c in self.cols])

    def create_record(self):
        data = self.form_data()
        if not data:
            messagebox.showwarning("Validation Error", "Fill in at least one field!")
            return
        try:
            db.create_row(self.table, data)
        except Exception as e:
            messagebox.showerror("Database Error", str(e))
            return
        self.clear_entries()
        self.populate_tree()

    def update_record(self):
        row_id = self.selected_id("update")
        if row_id is None:
            return
        try:
            # a blank field clears the value (NULL), so NOT NULL columns refuse it instead of storing ''
            db.update_row(self.table, row_id, {c: e.get() or None for c, e in self.entries.items()})
        except Exception as e:
            messagebox.showerror("Database Error", str(e))
            return
        self.clear_entries()
        self.populate_tree()

    def delete_record(self):
        row_id = self.selected_id("delete")
        if row_id is None:
            return
        if messagebox.askyesno("Confirm", "Are you sure you want to delete this record?"):
            try:
                db.delete_row(self.table, row_id)
            except Exception as e:  # e.g. still referenced by orders
                messagebox.showerror("Database Error", str(e))
                return
            self.clear_entries()
            self.populate_tree()

    def select_record(self, event):
        selected = self.tree.selection()
        if selected:
            values = self.tree.item(selected[0])["values"]
            self.clear_entries()
            for col, value in zip(self.cols, values[1:]):
                self.entries[col].insert(0, value)

    def clear_entries(self):
        for e in self.entries.values():
            e.delete(0, tk.END)


class HubWindow:
    """The main window: menu, one tab per table, a status bar with the database path."""

    def __init__(self, root):
        self.root = root
        root.title(TITLE)
        root.geometry("900x560")
        self.icon_set = set_icon(root)
        line = tkfont.nametofont("TkDefaultFont").metrics("linespace")
        ttk.Style(root).configure("Treeview", rowheight=line + 6)  # DPI-aware text needs taller rows
        self.small = tk.PhotoImage(file=ICON_PNG) if os.path.exists(ICON_PNG) else None

        menu = tk.Menu(root)
        file_menu = tk.Menu(menu, tearoff=False)
        file_menu.add_command(label="Database…", command=self.choose_db)
        file_menu.add_command(label="Seed demo data…", command=self.seed_demo)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=root.destroy)
        help_menu = tk.Menu(menu, tearoff=False)
        help_menu.add_command(label="Install for this user", command=lambda: self.run_installer(False))
        help_menu.add_command(label="Uninstall…", command=lambda: self.run_installer(True))
        help_menu.add_separator()
        help_menu.add_command(label="About", command=self.about)
        menu.add_cascade(label="File", menu=file_menu)
        menu.add_cascade(label="Help", menu=help_menu)
        root.config(menu=menu)

        self.status = tk.StringVar()
        ttk.Label(root, textvariable=self.status, anchor="w", padding=(8, 2)).pack(side="bottom", fill="x")
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill="both", expand=True)
        self.pages = []
        for table in db.SCHEMA:
            page = TablePage(self.notebook, table)
            self.notebook.add(page, text=table.title())
            self.pages.append(page)
        self.show_status()

    def counts(self):
        return {t: db.count_rows(t) for t in db.SCHEMA}

    def show_status(self):
        total = sum(self.counts().values())
        self.status.set(f"Database: {db.DB_PATH}  ·  {total:,} rows  ·  {__version__}")

    def refresh(self):
        for page in self.pages:
            page.populate_tree()
        self.show_status()

    def choose_db(self):
        path = filedialog.asksaveasfilename(
            parent=self.root, title="Shared database", initialfile=os.path.basename(db.DB_PATH),
            initialdir=os.path.dirname(db.DB_PATH), defaultextension=".db", confirmoverwrite=False,
            filetypes=[("SQLite database", "*.db"), ("All files", "*.*")])
        if not path:
            return
        db.DB_PATH = os.path.abspath(path)
        db.init_db()
        paths.save_settings({"db": db.DB_PATH}, APP_ID)
        self.refresh()

    def seed_demo(self):
        if not messagebox.askyesno("Seed demo data", f"Replace every row in\n{db.DB_PATH}\nwith the demo data?\n\n"
                                   "A dated backup copy is saved next to it first.", parent=self.root):
            return
        self.root.config(cursor="watch")
        self.root.update_idletasks()
        try:
            seed.seed()
        except Exception as e:  # e.g. the file is locked by another program mid-write
            messagebox.showerror("Seed failed", str(e), parent=self.root)
        finally:
            self.root.config(cursor="")
        self.refresh()

    def run_installer(self, remove):
        if remove and not messagebox.askyesno("Uninstall", f"Uninstall {NAME}?\nThe database is kept.", parent=self.root):
            return
        try:
            message = do_install(remove=remove)
        except Exception as e:
            messagebox.showerror("Installer", str(e), parent=self.root)
            return
        messagebox.showinfo("Installer", message, parent=self.root)
        if remove:
            self.root.destroy()

    def about(self):
        win = tk.Toplevel(self.root)
        win.title(f"About {NAME}")
        win.resizable(False, False)
        if self.small:
            win.big = self.small.zoom(3)  # 96 px of whole-pixel blocks
            ttk.Label(win, image=win.big).pack(padx=24, pady=(20, 8))
        text = (f"{NAME} {__version__}\n{PUBLISHER}\nACME: American Company Management Engine\n\nDatabase: {db.DB_PATH}\n\n{CREDIT}\n"
                "Code: AGPL-3.0. All data is fictional.")
        ttk.Label(win, text=text, justify="center", wraplength=420).pack(padx=24, pady=(0, 12))
        ttk.Button(win, text="OK", command=win.destroy).pack(pady=(0, 16))
        win.transient(self.root)


def windows_identity():
    """Own taskbar button and icon (not Python's), and crisp pixels on scaled displays."""
    if os.name != "nt":
        return
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(APP_ID)
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except (AttributeError, OSError):
        pass


def set_icon(root):
    """The pixel icon on the window, its taskbar button and every dialog; -> True when Windows shows it."""
    try:
        root.iconbitmap(default=ICON)  # class icon: every dialog and Toplevel
        root.iconbitmap(ICON)  # this window's own icons (WM_SETICON), which the taskbar uses
    except tk.TclError:
        return False
    if os.name != "nt":
        return True
    root.update_idletasks()
    hwnd = int(root.wm_frame(), 16)
    return bool(ctypes.windll.user32.SendMessageW(hwnd, 0x7F, 1, 0))  # WM_GETICON, ICON_BIG


def program():
    return installer.Program(APP_ID, NAME, __version__, PUBLISHER, installer.program_files(HERE, RUNTIME),
                             ["{dir}\\main.py"])


def do_install(remove=False, root=None, desktop=False, purge=False, quiet=False):
    plan = installer.plan(program(), HERE, root=root, desktop=desktop)
    if remove:
        plan = installer.located(plan)
        if installer.wizard_uninstaller(plan):
            # a setup made by ACME Wizard Maker installed it: its uninstaller keeps the files changed since
            return installer.run_uninstaller(plan, installer.uninstall_args(root, quiet, purge)) or f"{NAME} uninstalled."
        purge_dir = paths.data_dir(APP_ID) if purge else None
        gone = installer.uninstall(plan, purge_dir=purge_dir)
        return f"{NAME} uninstalled." + ("" if gone else " (It was not installed.)") + " The database is kept."
    installer.install(plan)
    return f"{NAME} {__version__} installed in {plan['install_dir']}. Find it in the Start menu under ACME Inc."


def parse(argv):
    ap = argparse.ArgumentParser(prog="main.py", description=NAME)
    ap.add_argument("--db", help="shared database file (default: saved setting or %%LOCALAPPDATA%%\\ACME Inc\\acme.db)")
    ap.add_argument("--version", action="store_true")
    ap.add_argument("--install", action="store_true", help="install for this user")
    ap.add_argument("--desktop-shortcut", action="store_true", help="with --install: add a desktop shortcut")
    ap.add_argument("--uninstall", action="store_true")
    ap.add_argument("--quiet", action="store_true", help="no message boxes")
    ap.add_argument("--purge", action="store_true", help="with --uninstall: also remove this program's settings")
    ap.add_argument("--root", help="sandbox: install under this folder instead (registry goes to registry.json)")
    ap.add_argument("--smoke", metavar="FILE", help="open the window, write a JSON report to FILE, close")
    return ap.parse_args(argv)


def tell(message, quiet):
    print(message)
    if not quiet and sys.stdout is None:  # pythonw (Start menu, Apps & features): no console to print to
        messagebox.showinfo(NAME, message)


def main(argv=None):
    args = parse(sys.argv[1:] if argv is None else argv)
    if args.version:
        tell(f"{NAME} {__version__}", args.quiet)
        return 0
    if args.install or args.uninstall:
        try:
            tell(do_install(args.uninstall, args.root, args.desktop_shortcut, args.purge, args.quiet), args.quiet)
        except installer.UninstallerFailed as e:  # its exit code goes on: 3 cancelled, 4 refused, ...
            tell(f"{NAME}: {e}", args.quiet or e.code == installer.CANCELLED)
            return e.code
        except Exception as e:
            tell(f"{NAME}: {e}", args.quiet)
            return 1
        return 0

    db.DB_PATH = paths.resolve_db(args.db, APP_ID)
    db.init_db()
    windows_identity()
    root = tk.Tk()
    window = HubWindow(root)
    if args.smoke:
        def report():
            data = {"app_id": APP_ID, "version": __version__, "title": root.title(), "icon_set": window.icon_set,
                    "source": "db", "db": db.DB_PATH, "counts": window.counts()}
            with open(args.smoke, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            root.destroy()
        root.after(500, report)
    root.mainloop()
    return 0


if __name__ == "__main__":
    sys.exit(main())

# ==== stamp v1 | author=kjFriday | hmac-sha256=f673f0ccf98b0fc1ad64aa545b85d079c86b3ce7f60ac8ac664996d0975f900f ====
