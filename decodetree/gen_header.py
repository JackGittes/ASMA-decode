import os
import json
import subprocess
from typing import List, Dict, Optional


def gen_headers(script_path: str, cfg_path: str,
                out_path: str, cur_dir: str) -> None:
    assert isinstance(cfg_path, str)
    with open(cfg_path, "r") as fp:
        cfgs: List[Dict] = json.load(fp)

    script_path = os.path.abspath(script_path)
    abs_path = os.path.abspath(out_path)
    for cfg in cfgs:
        arch: str = cfg["arch"]
        files: List[Dict] = cfg["files"]
        out_dir = os.path.join(abs_path, arch)
        os.makedirs(out_dir, exist_ok=True)
        for decode_tree in files:
            dt_src: str = decode_tree["src"]
            args: Optional[List[str]] = decode_tree["extra_args"]
            if isinstance(args, list):
                file_name = ""
                for arg in args:
                    if arg.startswith("--static-decode=") or \
                            arg.startswith("--decode="):
                        file_name = arg.split("=")[1].replace("_", "-")
                        break
                args = " ".join(args)
            elif isinstance(args, str):
                file_name = args.split("=")[1].replace("_", "-")
            else:
                raise TypeError("Unknown type %s" % type(args))
            out_name = os.path.join(out_dir, file_name + ".c.inc")

            if arch in {"arm32", "arm64"}:
                arch_arg = "arm"
            elif arch in {"riscv"}:
                arch_arg = "riscv"
            else:
                raise RuntimeError(f"Unknown arch: {arch}")
            dt_src = os.path.join(cur_dir, "../target/%s/dt/" % arch_arg, dt_src)  # noqa: E501
            args = " %s" % dt_src + " " + args + " --output %s" % out_name
            args += (" --arch=%s" % arch_arg)
            subprocess.run("python3 " + script_path + " %s" % args, shell=True)


if __name__ == "__main__":
    cur_path = os.path.abspath(__file__)
    cur_dir = cur_path[:len(cur_path) - len(os.path.basename(__file__))]
    cur_script_path = os.path.join(cur_dir, "decodetree-asma.py")
    cur_json_path = os.path.join(cur_dir, "decode.json")
    cur_out_path = os.path.join(cur_dir, "../include/gen/")

    gen_json = cur_dir + "/gen.json"
    if os.path.exists(gen_json):
        os.remove(gen_json)
    gen_headers(script_path=cur_script_path, cfg_path=cur_json_path,
                out_path=cur_out_path, cur_dir=cur_dir)
