import mmap
import ctypes
import os
from typing import Dict, Optional
from io import IOBase
from ctypes import CDLL
from .c_struct import RISCVCPUConfig, RISCVDisasContext


class ASMADecoderWapper:
    def __init__(self, so_path: str,
                 elf_path: Optional[str] = None,
                 sym_off: int = 0,
                 sym_size: int = 0) -> None:
        self.clib: CDLL = CDLL(so_path)
        self.cpu_cfg: RISCVCPUConfig = RISCVCPUConfig()
        self.ctx = RISCVDisasContext()

        self._init_dummpy_ctx()

        assert isinstance(elf_path, str)
        assert isinstance(sym_off, int)
        assert isinstance(sym_size, int)
        self.sym_off: int = sym_off
        self.sym_size: int = sym_size

    def _init_dummpy_ctx(self) -> None:
        self.ctx.ol = 1
        self.ctx.xl = 1
        self.ctx.misa_ext = 0xffffffffffffffff
        self.ctx.cur_insn_len = 0
        self.ctx.pc_next = 0
        self.ctx.cfg_ptr = ctypes.pointer(self.cpu_cfg)

    def set_disas_position(self,
                           base: int = 0,
                           offset: int = 0,
                           size: int = 0) -> None:
        assert isinstance(base, int) and base > 0
        assert isinstance(offset, int) and (base + offset) > 0
        assert isinstance(size, int) and size > 0
        self.ctx.base_off = base + offset
        self.sym_size = size

    def init_from_raw_bytes(self, bin_path: str) -> None:
        with open(bin_path, "rb+") as fp:
            f_ptr: ctypes._Pointer = load_elf_section(fp)
            self.sym_size = fp.tell()
        self.ctx.base_off = ctypes.addressof(f_ptr.contents)

    def disas(self, single_step: bool = False) -> bool:
        assert isinstance(single_step, bool)
        ctx_ptr = ctypes.pointer(ctx)
        if single_step:
            self.clib.riscv_decode_insn(ctx_ptr)
            return True
        while ctx.pc_next < self.sym_size:
            self.clib.riscv_decode_insn(ctx_ptr)


def load_elf_section(fd: IOBase) -> ctypes.c_uint64:
    buf: IOBase = mmap.mmap(fd.fileno(), 0, mmap.MAP_SHARED,
                            prot=mmap.PROT_WRITE)
    buf_pointer = ctypes.pointer(ctypes.c_uint64.from_buffer(buf))
    return buf_pointer


def gen_ctypes_structs(name: str, flds: Dict[str, str]) -> str:
    indent: str = " " * 4
    gen_struct = "class %s(ctypes.Structure):\n" % name
    gen_begin: str = indent + "_fields_ = ["
    gen_struct += gen_begin

    scope_sym: str = "::"

    for fld_idx, (fld_k, fld_ty) in enumerate(flds.items(), start=1):
        starting = " " * len(gen_begin) if fld_idx > 1 else ""
        ending = "\n" if fld_idx < len(flds) else ""
        if scope_sym in fld_ty:
            nested_n: int = fld_ty.count(scope_sym)
            fld_tys = fld_ty.split(scope_sym)
            fld_ty = ""
            for ty_idx, ty in enumerate(fld_tys, start=1):
                if ty_idx == 1:
                    fld_ty += (ty + "(")
                elif ty_idx > 1 and ty_idx < len(fld_tys):
                    fld_ty += ("ctypes." + ty + "(")
                elif ty_idx == len(fld_tys):
                    fld_ty += ("ctypes." + ty)
                else:
                    raise RuntimeError("Impossible path reached.")
            fld_ty += (")" * nested_n)
        gen_struct += starting + '("%s", ctypes.%s),%s' \
                                 % (fld_k, fld_ty, ending)
    gen_struct += "]\n"
    return gen_struct


def get_cpu_cfg():
    import json
    with open("./target/riscv/cpu.json", "r") as fp:
        py_gen_info = json.load(fp)

    mod_imports = {"ctypes"}

    _gen_structs: str = ""
    cpu_cfg: Dict[str, Dict] = py_gen_info["cpu_cfg"]
    _gen_structs += gen_ctypes_structs(cpu_cfg["name"], cpu_cfg["fields"])
    _gen_structs += "\n\n"
    disas_ctx: Dict[str, Dict] = py_gen_info["context"]
    _gen_structs += gen_ctypes_structs(disas_ctx["name"], disas_ctx["fields"])

    imp_str = ""
    for imp in mod_imports:
        imp_str += ("import %s\n" % imp)
    imp_str += "\n\n"

    return imp_str + _gen_structs


if __name__ == "__main__":
    # mod = get_cpu_cfg()
    # print(mod)
    cur_path = os.path.abspath(__file__)
    cur_dir = cur_path[:len(cur_path) - len("decode.py")]
    # gen_mod_path: str = os.path.join(cur_dir, "c_struct.py")
    # with open(gen_mod_path, "w") as fp:
    #     fp.write(mod)

    # codeobj = compile(open(gen_mod_path).read(), gen_mod_path, 'exec')
    # globs = {}
    # locs = {}
    # exec(codeobj, globs, locs)
    # cls = globs['RISCVDisasContext']
    trans_clib = CDLL(os.path.join(cur_dir, "..", "libtranslate.so"))
    trans_lib = trans_clib
    with open(os.path.join(cur_dir, "../", "test_bytes.bin"), "rb+") as fp:
        f_ptr = load_elf_section(fp)

    from c_struct import RISCVCPUConfig, RISCVDisasContext
    cpu_cfg = RISCVCPUConfig()
    ctx = RISCVDisasContext()
    ctx.ol = 1
    ctx.xl = 1
    ctx.misa_ext = 0xffffffffffffffff
    ctx.cur_insn_len = 0
    ctx.pc_next = 0
    ctx.base_off = ctypes.addressof(f_ptr.contents) + 4
    print(ctypes.addressof(f_ptr.contents))
    # print(hex(f_ptr))
    # ctx.base_off = f_ptr
    ctx.cfg_ptr = ctypes.pointer(cpu_cfg)
    trans_clib.riscv_decode_insn(ctypes.pointer(ctx))
    ctx_ptr = ctypes.pointer(ctx)
    while ctx.pc_next < 68:
        trans_clib.riscv_decode_insn(ctx_ptr)
    print(ctx.pc_next)
