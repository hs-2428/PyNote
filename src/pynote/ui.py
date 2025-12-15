# src/pynote/ui.py
"""
UI components (menus, dialogs) for PyNote.
"""

import tkinter as tk
from tkinter import messagebox, simpledialog
from tkinter import ttk
from pathlib import Path
from . import utils


class AboutDialog:
    """About dialog for PyNote."""
    
    def __init__(self, parent):
        self.parent = parent
        self.dialog = tk.Toplevel(parent)
        self.dialog.title('About PyNote')
        self.dialog.geometry('300x200')
        self.dialog.resizable(False, False)
        self._create_widgets()
    
    def _create_widgets(self):
        tk.Label(
            self.dialog,
            text='PyNote',
            font=('Arial', 16, 'bold')
        ).pack(pady=10)
        
        tk.Label(
            self.dialog,
            text='A Beginner-Friendly Desktop Text Editor',
            font=('Arial', 10)
        ).pack(pady=5)
        
        tk.Label(
            self.dialog,
            text='Version 0.1.0',
            font=('Arial', 9)
        ).pack(pady=5)
        
        tk.Label(
            self.dialog,
            text='Built with Python + Tkinter',
            font=('Arial', 8)
        ).pack(pady=5)
        
        tk.Button(
            self.dialog,
            text='OK',
            command=self.dialog.destroy,
            width=10
        ).pack(pady=20)


class GoToLineDialog:
    """Go to line number dialog."""
    
    def __init__(self, parent, max_lines):
        self.parent = parent
        self.max_lines = max_lines
        self.result = None
        self.dialog = tk.Toplevel(parent)
        self.dialog.title('Go to Line')
        self.dialog.geometry('250x100')
        self.dialog.resizable(False, False)
        self._create_widgets()
    
    def _create_widgets(self):
        tk.Label(
            self.dialog,
            text=f'Enter line number (1-{self.max_lines}):'
        ).pack(pady=10)
        
        self.entry = tk.Entry(self.dialog, width=20)
        self.entry.pack(pady=5)
        self.entry.focus()
        self.entry.bind('<Return>', lambda e: self._ok())
        
        button_frame = tk.Frame(self.dialog)
        button_frame.pack(pady=10)
        
        tk.Button(
            button_frame,
            text='OK',
            command=self._ok,
            width=8
        ).pack(side='left', padx=5)
        
        tk.Button(
            button_frame,
            text='Cancel',
            command=self.dialog.destroy,
            width=8
        ).pack(side='left', padx=5)
    
    def _ok(self):
        try:
            line_num = int(self.entry.get())
            if 1 <= line_num <= self.max_lines:
                self.result = line_num
                self.dialog.destroy()
            else:
                messagebox.showerror(
                    'Error',
                    f'Line number must be between 1 and {self.max_lines}'
                )
        except ValueError:
            messagebox.showerror('Error', 'Please enter a valid number')


def show_about(parent):
    """Show about dialog."""
    AboutDialog(parent)


class SearchDialog:
    """Dialog for searching across project files and showing clickable results."""

    def __init__(self, parent, app, root_path=None):
        self.parent = parent
        self.app = app
        self.root_path = Path(root_path) if root_path else Path.cwd()
        self.dialog = tk.Toplevel(parent)
        self.dialog.title('Find in Files')
        self.dialog.geometry('800x400')
        self._create_widgets()

    def _create_widgets(self):
        frm = tk.Frame(self.dialog)
        frm.pack(fill='x', padx=8, pady=6)

        tk.Label(frm, text='Search:').grid(row=0, column=0, sticky='w')
        self.query = tk.Entry(frm, width=40)
        self.query.grid(row=0, column=1, sticky='w')

        tk.Label(frm, text='File types (comma, e.g. .py,.md):').grid(row=0, column=2, sticky='w', padx=(10, 0))
        self.filetypes = tk.Entry(frm, width=20)
        self.filetypes.grid(row=0, column=3, sticky='w')

        self.regex_var = tk.BooleanVar(value=False)
        self.ignore_case_var = tk.BooleanVar(value=True)
        tk.Checkbutton(frm, text='Regex', variable=self.regex_var).grid(row=1, column=1, sticky='w')
        tk.Checkbutton(frm, text='Ignore case', variable=self.ignore_case_var).grid(row=1, column=2, sticky='w')

        tk.Label(frm, text='Context lines:').grid(row=1, column=3, sticky='e')
        self.context_spin = tk.Spinbox(frm, from_=0, to=10, width=4)
        self.context_spin.grid(row=1, column=4, sticky='w')

        btn_frame = tk.Frame(self.dialog)
        btn_frame.pack(fill='x', padx=8)
        tk.Button(btn_frame, text='Search', command=self._on_search).pack(side='left')
        tk.Button(btn_frame, text='Close', command=self.dialog.destroy).pack(side='left', padx=6)

        # Results
        cols = ('path', 'line', 'preview')
        self.tree = ttk.Treeview(self.dialog, columns=cols, show='headings')
        self.tree.heading('path', text='Path')
        self.tree.heading('line', text='Line')
        self.tree.heading('preview', text='Preview')
        self.tree.column('path', width=350)
        self.tree.column('line', width=50, anchor='center')
        self.tree.column('preview', width=380)
        self.tree.pack(fill='both', expand=True, padx=8, pady=8)
        self.tree.bind('<Double-1>', self._on_activate)

        # simple status
        self.status = tk.StringVar()
        ttk.Label(self.dialog, textvariable=self.status).pack(fill='x', padx=8, pady=(0, 8))

    def _on_search(self):
        q = self.query.get().strip()
        if not q:
            messagebox.showinfo('Find in Files', 'Please enter a search query')
            return

        filetypes = [t.strip() for t in self.filetypes.get().split(',') if t.strip()]
        if filetypes == []:
            filetypes = None

        regex = bool(self.regex_var.get())
        ignore_case = bool(self.ignore_case_var.get())
        try:
            context_lines = int(self.context_spin.get())
        except Exception:
            context_lines = 1

        self.status.set('Searching...')
        try:
            results = utils.full_text_search(self.root_path, q, regex=regex, ignore_case=ignore_case, file_extensions=filetypes, recursive=True, context_lines=context_lines)
        except Exception as e:
            messagebox.showerror('Search error', str(e))
            self.status.set('')
            return

        # clear
        for i in self.tree.get_children():
            self.tree.delete(i)

        for r in results:
            preview_parts = []
            if r.get('pre_context'):
                preview_parts.append(' / '.join(r['pre_context']))
            preview_parts.append(r.get('line', ''))
            if r.get('post_context'):
                preview_parts.append(' / '.join(r['post_context']))
            preview = '  ← '.join([p for p in preview_parts if p])
            self.tree.insert('', 'end', values=(r['path'], r['line_no'], preview), tags=('match',))

        self.status.set(f'{len(results)} matches')

    def _on_activate(self, event):
        sel = self.tree.selection()
        if not sel:
            return
        item = sel[0]
        path, line_no, preview = self.tree.item(item, 'values')
        try:
            ln = int(line_no)
        except Exception:
            ln = 1
        # ask app to open file at line
        try:
            self.app.open_file_at(path, ln)
        except Exception as e:
            messagebox.showerror('Open file', f'Failed to open file: {e}')

