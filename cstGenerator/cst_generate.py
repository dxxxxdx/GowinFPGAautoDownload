# Simplified Verilog module parser
# Usage:
#   - Import: from cstGenerator.cst_generate import parse_verilog_modules, VerilogModule
#       modules = parse_verilog_modules('path/to/file.v')
#       for m in modules:
#           print(m)            # human-friendly
#           data = m.as_dict()  # programmatic
#   - CLI: run this script directly to pick a file via GUI (tkinter) or type path in console.

import re
from typing import List, Tuple, Optional


def strip_comments(s: str) -> str:
    """Remove // line comments and /* */ block comments."""
    s = re.sub(r'//.*', '', s)
    s = re.sub(r'/\*.*?\*/', '', s, flags=re.S)
    return s


class VerilogModule:
    """Lightweight representation of a Verilog module.

    Attributes:
        name: module name
        ports: list of (port_name, direction) where direction is 'input'|'output'|'inout' or 'unknown'
    """

    def __init__(self, name: str, ports: Optional[List[Tuple[str, str]]] = None):
        self.name = name
        self.ports = ports or []

    def as_dict(self) -> dict:
        return {"name": self.name, "ports": [{"name": n, "dir": d} for n, d in self.ports]}

    def pretty(self) -> str:
        if not self.ports:
            return f"Module {self.name}: (no ports)"
        lines = [f"Module {self.name}:\n  Ports:"]
        for n, d in self.ports:
            lines.append(f"    {d:6} {n}")
        return "\n".join(lines)

    def __str__(self) -> str:
        return self.pretty()

    def __repr__(self) -> str:
        return f"VerilogModule(name={self.name!r}, ports={self.ports!r})"


# --- parsing helpers ---

def _parse_ports_from_block(port_block: str, full_text: str) -> List[Tuple[str, str]]:
    """Parse the port block text and return list of (port_name, direction).

    Supports ANSI-style declarations (direction in the module header) and
    non-ANSI style (names listed in header and directions in body).
    """
    # ANSI-style: direction appears in the header
    ansi_pat = re.compile(
        r"\b(input|output|inout)\b"                # direction
        r"(?:\s+(?:wire|reg|logic))?"               # optional type
        r"(?:\s*\[.*?])?"                          # optional range
        r"\s+([^;,]+)",                             # comma-separated names
        flags=re.S,
    )

    ports: List[Tuple[str, str]] = []
    ansi_found = False
    for direction, names in ansi_pat.findall(port_block):
        ansi_found = True
        for nm in [x.strip() for x in names.split(',') if x.strip()]:
            # strip trailing ranges like "foo[3:0]" or "foo [3:0]"
            nm = re.sub(r"\s*\[.*?]\s*$", "", nm).strip()
            ports.append((nm, direction))

    if ansi_found:
        return ports

    # Non-ANSI: header only has names; find directions in the body
    raw_names = [x.strip() for x in port_block.split(',') if x.strip()]
    dir_pat = re.compile(
        r"\b(input|output|inout)\b"                # direction
        r"(?:\s+(?:wire|reg|logic))?"               # optional type
        r"(?:\s*\[.*?])?\s+([^;]+);",             # names up to semicolon
        flags=re.S,
    )

    dir_map = {}
    for direction, names in dir_pat.findall(full_text):
        for nm in [x.strip() for x in names.split(',') if x.strip()]:
            nm = re.sub(r"\s*\[.*?]\s*$", "", nm).strip()
            dir_map[nm] = direction

    results: List[Tuple[str, str]] = []
    for nm in raw_names:
        clean = re.sub(r"\s*\[.*?]\s*$", "", nm).strip()
        results.append((clean, dir_map.get(clean, 'unknown')))

    return results


def parse_verilog_modules(file_path: str) -> List[VerilogModule]:
    """Parse a Verilog file and return a list of VerilogModule objects.

    The parser looks for patterns like:
        module name ( ... );
    and extracts the header port block. It's heuristic-based and intended for
    common Verilog styles (ANSI and non-ANSI); it may not handle every
    corner-case of SystemVerilog syntax.
    """
    text = open(file_path, 'r', encoding='utf-8').read()
    text = strip_comments(text)

    # find all module headers with their port blocks
    mod_pat = re.compile(
        r"module\s+([a-zA-Z_]\w*)"          # module name
        r"(?:\s*#\s*\([^)]*\))?"          # optional parameter block
        r"\s*\((.*?)\)\s*;",              # port block (non-greedy)
        flags=re.S,
    )

    modules: List[VerilogModule] = []
    for m in mod_pat.finditer(text):
        name = m.group(1)
        port_block = m.group(2)
        ports = _parse_ports_from_block(port_block, text)
        modules.append(VerilogModule(name, ports))

    return modules


# Backwards-compatible helper: return the first/top module (or None)
def parse_verilog_top(file_path: str) -> Tuple[Optional[str], List[Tuple[str, str]]]:
    mods = parse_verilog_modules(file_path)
    if not mods:
        return None, []
    top = mods[0]
    return top.name, top.ports


def gui_select_and_parse(filetypes=None, allow_console_fallback: bool = True):
    """Open a blocking GUI file-selection dialog and return parsed modules.

    Returns:
        List[VerilogModule] parsed from the selected file, or [] if no file selected.

    Parameters:
        filetypes: optional list of (label, pattern) tuples passed to filedialog.
        allow_console_fallback: if True and tkinter is unavailable, prompt for path on console.
    """
    if filetypes is None:
        filetypes = [('Verilog files', '*.v *.sv'), ('All files', '*.*')]

    try:
        import tkinter as tk
        from tkinter import filedialog
        root = tk.Tk()
        root.withdraw()
        path = filedialog.askopenfilename(title='Select Verilog file', filetypes=filetypes)
    except Exception:
        if allow_console_fallback:
            try:
                path = input('Enter Verilog file path: ').strip()
            except Exception:
                path = ''
        else:
            return []

    if not path:
        return []

    return parse_verilog_modules(path)


# --- CLI entrypoint ---
if __name__ == '__main__':
    # GUI file selector with console fallback
    verilog_file = ''
    try:
        import tkinter as tk
        from tkinter import filedialog
        root = tk.Tk()
        root.withdraw()
        verilog_file = filedialog.askopenfilename(
            title='Select Verilog file',
            filetypes=[('Verilog files', '*.v *.sv'), ('All files', '*.*')],
        )
    except Exception:
        try:
            verilog_file = input('Enter Verilog file path: ').strip()
        except Exception:
            verilog_file = ''

    if not verilog_file:
        print('No file selected, exiting.')
        import sys
        sys.exit(0)

    modules = parse_verilog_modules(verilog_file)
    if not modules:
        print('No modules found in file.')
        import sys
        sys.exit(0)

    print(f"Found {len(modules)} module(s) in '{verilog_file}':\n")
    for mod in modules:
        print(mod.pretty())
        print()
