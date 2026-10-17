"""ACME Inc. CRUD desktop app — one tab per table, same Add/Update/Delete/Clear flow as before.

Run `python seed.py` for mock data and `python api.py` to serve it to the other projects.
"""

import tkinter as tk
from tkinter import messagebox, ttk

import db


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
            db.update_row(self.table, row_id, {c: e.get() for c, e in self.entries.items()})
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


# --- Main Application Window ---
if __name__ == "__main__":
    db.init_db()

    root = tk.Tk()
    root.title("ACME Inc. — CRUD Platform")
    root.geometry("900x560")

    notebook = ttk.Notebook(root)
    notebook.pack(fill="both", expand=True)
    for table in db.SCHEMA:
        notebook.add(TablePage(notebook, table), text=table.title())

    root.mainloop()
