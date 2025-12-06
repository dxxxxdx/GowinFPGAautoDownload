"""Simple GUI to map Verilog module ports to board I/Os and generate CST file.

Usage:
    python -m cstGenerator.cst_gui

Features:
- Pick a Verilog file (opens file dialog).
- Choose one module from that file.
- For each port, choose a board IO from the target device list (GW1NSR4C_QN48).
- Save a generated CST file (text) using the mapping.

This GUI is intentionally minimal and synchronous (blocking file dialogs).
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import List
import os

from cstGenerator.cst_generate import parse_verilog_modules
from cstGenerator.cst_config import GW1NSR4C_QN48


class PortMappingRow:
    def __init__(self, parent, port_name: str, io_options: List[str]):
        self.port_name = port_name
        self.var = tk.StringVar(value="")
        frame = tk.Frame(parent)
        lbl = tk.Label(frame, text=port_name, width=25, anchor='w')
        lbl.pack(side='left', padx=(2, 8))
        opt = ttk.Combobox(frame, values=io_options, textvariable=self.var, width=20)
        opt.pack(side='left', padx=(0, 8))
        # allow clearing selection
        clear_btn = tk.Button(frame, text='Clear', command=lambda: self.var.set(''))
        clear_btn.pack(side='left')
        self.frame = frame

    def pack(self, **kwargs):
        self.frame.pack(**kwargs)

    def get(self):
        return self.port_name, self.var.get()


class App:
    def __init__(self, root):
        self.root = root
        root.title('Verilog -> CST mapper')
        self.device = GW1NSR4C_QN48.get_instance()

        # Top controls
        top = tk.Frame(root)
        top.pack(fill='x', pady=6)  # type: ignore[attr-defined]
        self.file_lbl = tk.Label(top, text='No file selected', anchor='w')
        self.file_lbl.pack(side='left', padx=6)  # type: ignore[attr-defined]
        btn = tk.Button(top, text='Open Verilog...', command=self.open_verilog)
        btn.pack(side='right', padx=6)  # type: ignore[attr-defined]

        # Module selection
        mid = tk.Frame(root)
        mid.pack(fill='x', pady=6)  # type: ignore[attr-defined]
        lbl_mod = tk.Label(mid, text='Module:')
        lbl_mod.pack(side='left', padx=(6, 4))  # type: ignore[attr-defined]
        self.module_var = tk.StringVar(value='')
        self.module_combo = ttk.Combobox(mid, textvariable=self.module_var, state='readonly')
        self.module_combo.pack(side='left', padx=4)  # type: ignore[attr-defined]
        self.module_combo.bind('<<ComboboxSelected>>', lambda e: self.module_selected())

        # Port mapping area (scrollable)
        self.map_frame = tk.Frame(root)
        self.map_frame.pack(fill='both', expand=True, padx=6, pady=6)  # type: ignore[attr-defined]
        self._build_scroll_area(self.map_frame)

        # Bottom controls
        bottom = tk.Frame(root)
        bottom.pack(fill='x', pady=6)  # type: ignore[attr-defined]
        self.status = tk.Label(bottom, text='Ready', anchor='w')
        self.status.pack(side='left', padx=6)  # type: ignore[attr-defined]
        save_btn = tk.Button(bottom, text='Generate CST...', command=self.generate_cst)
        save_btn.pack(side='right', padx=6)  # type: ignore[attr-defined]

        # internal state
        self.modules = []  # list of VerilogModule
        self.mapping_rows: List[PortMappingRow] = []

    def _build_scroll_area(self, parent):
        # create a canvas with a vertical scrollbar and a frame inside for rows
        canvas = tk.Canvas(parent, borderwidth=0)
        vsb = tk.Scrollbar(parent, orient='vertical', command=canvas.yview)
        canvas.configure(yscrollcommand=vsb.set)
        vsb.pack(side='right', fill='y')  # type: ignore[attr-defined]
        canvas.pack(side='left', fill='both', expand=True)  # type: ignore[attr-defined]
        inner = tk.Frame(canvas)
        canvas.create_window((0, 0), window=inner, anchor='nw')  # type: ignore[attr-defined]

        def on_config(event):
            canvas.configure(scrollregion=canvas.bbox('all'))
        inner.bind('<Configure>', on_config)  # type: ignore[attr-defined]
        self.inner = inner

    def open_verilog(self):
        path = filedialog.askopenfilename(title='Select Verilog file', filetypes=[('Verilog', '*.v *.sv'), ('All', '*.*')])
        if not path:
            return
        self.file_lbl.config(text=os.path.basename(path))
        try:
            self.modules = parse_verilog_modules(path)
        except Exception as e:
            messagebox.showerror('Error', f'Failed to parse Verilog: {e}')
            return
        names = [m.name for m in self.modules]
        self.module_combo['values'] = names
        if names:
            self.module_combo.current(0)
            self.module_selected()
        self.status.config(text=f'Loaded {len(self.modules)} module(s)')

    def module_selected(self):
        sel = self.module_var.get()
        mod = next((m for m in self.modules if m.name == sel), None)
        # clear existing rows
        for r in self.mapping_rows:
            r.frame.destroy()
        self.mapping_rows.clear()
        if mod is None:
            return
        # build options from device ports
        io_options = [''] + [p.name for p in self.device.list_ports()]
        # create a row per port
        for p, _ in mod.ports:
            row = PortMappingRow(self.inner, p, io_options)
            row.pack(fill='x', pady=2)  # type: ignore[arg-type]
            self.mapping_rows.append(row)
        self.status.config(text=f'Module {mod.name}: {len(mod.ports)} port(s)')

    def get_mapping(self):
        mapping = {}
        for row in self.mapping_rows:
            port, io = row.get()
            mapping[port] = io
        return mapping

    def generate_cst(self):
        sel = self.module_var.get()
        if not sel:
            messagebox.showwarning('No module', 'Please select a module first')
            return
        mapping = self.get_mapping()
        save_path = filedialog.asksaveasfilename(title='Save CST file', defaultextension='.cst', filetypes=[('CST', '*.cst'), ('Text', '*.txt'), ('All', '*.*')])
        if not save_path:
            return
        try:
            self.device.out_put_cst(mapping, save_path, module_name=sel)
        except Exception as e:
            messagebox.showerror('Error', f'Failed to write CST: {e}')
            return
        messagebox.showinfo('Saved', f'CST saved to {save_path}')
        self.status.config(text=f'Saved {os.path.basename(save_path)}')


def main():
    root = tk.Tk()
    app = App(root)
    root.geometry('700x500')  # type: ignore[attr-defined]
    root.mainloop()


if __name__ == '__main__':
    main()
