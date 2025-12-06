class IOConfig:
    def __init__(self, name, loc, io_type, pull_mode="NONE", drive=None):
        self.name = name
        self.loc = loc
        self.io_type = io_type
        self.pull_mode = pull_mode
        self.drive = drive

    def __repr__(self):
        return (f"IOConfig(name={self.name}, loc={self.loc}, "
                f"io_type={self.io_type}, pull_mode={self.pull_mode}, drive={self.drive})")


class GW1NSR4C_QN48:
    _instance = None   # 单例引用

    def __init__(self):
        if GW1NSR4C_QN48._instance is not None:
            raise Exception("This class is a singleton! Use get_instance().")
        self.ports = {}

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = GW1NSR4C_QN48()
            cls._instance._register_all()
        return cls._instance

    def register(self, io_config: IOConfig):
        self.ports[io_config.name] = io_config

    def get(self, name):
        return self.ports.get(name)

    def list_ports(self):
        return list(self.ports.values())

    def _register_all(self):
        """一次性注册所有 CST约束端口"""
        # MCU快速时钟
        self.register(IOConfig("mcu_fast_clk", 41, "LVCMOS33", "NONE"))
        # SW9控制使能FPGA
        self.register(IOConfig("fpga_en_sw9", 33, "LVCMOS25", "UP"))
        # 慢速FPGA时钟
        self.register(IOConfig("fpga_slow_clk", 16, "LVCMOS18", "NONE"))

        # FO7 - FO0
        for name, loc in zip(
            ["FO7","FO6","FO5","FO4","FO3","FO2","FO1","FO0"],
            [13,17,18,19,20,21,22,23]
        ):
            self.register(IOConfig(name, loc, "LVCMOS18", "DOWN"))

        # SW1 - SW8
        for name, loc in zip(
            ["SW1","SW2","SW3","SW4","SW5","SW6","SW7","SW8"],
            [27,28,29,30,35,34,32,31]
        ):
            self.register(IOConfig(name, loc, "LVCMOS25", "DOWN"))

        # MTF6 - MTF0
        self.register(IOConfig("MTF6", 40, "LVCMOS33", "UP"))
        self.register(IOConfig("MTF5", 39, "LVCMOS33", "UP"))
        self.register(IOConfig("MTF4", 10, "LVCMOS33", "NONE"))
        self.register(IOConfig("MTF3", 42, "LVCMOS33", "UP"))
        self.register(IOConfig("MTF2", 43, "LVCMOS33", "UP"))


        self.register(IOConfig("MTF1", 46, "LVCMOS33", "UP"))
        self.register(IOConfig("MTF0", 44, "LVCMOS33", "UP"))

        # SPI pads (防呆设为输入)
        self.register(IOConfig("SPI_MISO_pad", 47, "LVCMOS33", "UP"))
        self.register(IOConfig("SPI_MOSI_pad", 48, "LVCMOS33", "UP"))
        self.register(IOConfig("SPI_SCK_pad", 1, "LVCMOS33", "UP"))


    def out_put_cst(self, mapping: dict, file_path: str, module_name: str = None):
        """输出符合示例规范的 CST 约束文本并写入文件。

        mapping: dict mapping from module port name -> board IO name (the keys of self.ports)
        file_path: destination path to write CST text
        module_name: optional, used in header comments
        """
        from datetime import datetime

        # helper: map IO standard to bank voltage string
        BANK_VCCIO = {
            'LVCMOS33': '3.3',
            'LVCMOS25': '2.5',
            'LVCMOS18': '1.8'
        }

        def _io_port_line(name: str, cfg: IOConfig) -> str:
            parts = [f'IO_PORT "{name}"', f'IO_TYPE={cfg.io_type}', f'PULL_MODE={cfg.pull_mode}']
            if cfg.drive is not None:
                parts.append(f'DRIVE={cfg.drive}')
            # add BANK_VCCIO if known
            bank = BANK_VCCIO.get(cfg.io_type)
            if bank:
                parts.append(f'BANK_VCCIO={bank}')
            return ' '.join(parts) + ';'

        def _io_loc_line(name: str, cfg: IOConfig) -> str:
            return f'IO_LOC "{name}" {cfg.loc};'

        now = datetime.now()
        created_time = now.strftime('%a %m %d %H:%M:%S %Y')

        header_lines = [
            '//Copyright (C)2014-2025 Gowin Semiconductor Corporation. //All rights reserved.',
            '//File Title: Physical Constraints file',
            '//Tool Version: V1.9.11.03 Education',
            '//Part Number: GW1NSR-LV4CQN48PC6/I5',
            '//Device: GW1NSR-4C',
            f'//Created Time: {created_time}',
            ''
        ]

        body_lines = []
        # optional module comment
        if module_name:
            body_lines.append(f'// Module: {module_name}')

        # generate entries in the order of mapping keys
        used_ios = set()
        for port, io_name in mapping.items():
            if not io_name:
                body_lines.append(f'// {port} -> UNASSIGNED')
                continue
            cfg = self.get(io_name)
            if cfg is None:
                body_lines.append(f'// {port} -> UNKNOWN_IO({io_name})')
                continue
            # Use Verilog port name for CST entries; use board cfg for loc/type/etc.
            body_lines.append(_io_loc_line(port, cfg))
            body_lines.append(_io_port_line(port, cfg))
            # annotate original board IO name and pin for traceability
            body_lines.append(f'// mapped to board IO: {io_name} (pin {cfg.loc})')
            # duplicate usage warning (board IO reused)
            if io_name in used_ios:
                body_lines.append(f'// WARNING: board IO {io_name} reused by port {port}')
            used_ios.add(io_name)

        # write file combining header and body
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(header_lines + body_lines))

        return file_path
