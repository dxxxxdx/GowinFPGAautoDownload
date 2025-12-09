import os
import sys
import subprocess
from pathlib import Path

import cstGenerator.cst_gui


def main():
    # 脚本目录
    script_dir = Path(__file__).resolve().parent
    # 构建 exe 的相对路径：Digital/Digital/Digital.exe
    exe_path = script_dir / "Digital" / "Digital" / "Digital.exe"

    if not exe_path.exists():
        print(f"错误：找不到可执行文件：{exe_path}", file=sys.stderr)
        return 1

    try:
        subprocess.Popen([str(exe_path)])
        print(f"已启动：{exe_path}")
        cstGenerator.cst_gui.main()
        return 0
    except Exception as e:
        print(f"启动失败：{e}", file=sys.stderr)
        return 2

if __name__ == "__main__":
    sys.exit(main())
