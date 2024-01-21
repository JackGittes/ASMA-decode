#include <iostream>
#include <fstream>
#include <string>
#include <vector>

extern "C" {
#include "cpu_cfg.h"
#include "translate.h"
}

std::vector<char>
get_binary_pointer(const std::string &file_path) {
    std::ifstream file(file_path, std::ios::binary | std::ios::ate);
    std::streamsize size = file.tellg();
    file.seekg(0, std::ios::beg);
    std::vector<char> buf(size);
    file.read(buf.data(), size);
    return buf;
}

int main() {
    RISCVCPUConfig rv_cfg;
    DisasContext ctx;
    ctx.ol = MXL_RV32;
    ctx.xl = ctx.ol;

    ctx.cfg_ptr = &rv_cfg;
    riscv_set_misa(&ctx, RVI);
    riscv_set_misa(&ctx, RVM);
    riscv_set_misa(&ctx, RVA);
    riscv_set_misa(&ctx, RVC);
    riscv_set_misa(&ctx, RVF);
    riscv_set_misa(&ctx, RVD);
    riscv_set_misa(&ctx, RVS);
    riscv_set_misa(&ctx, RVH);
    riscv_set_misa(&ctx, RVG);

    std::vector<char> buf_ptr = get_binary_pointer("/home/zhaomingxin/CodeBase/Tools/CAsmParser/test_bytes.bin");
    ctx.base_off = (uint64_t) &buf_ptr[0];
    ctx.pc_next = 0;

    std::cout << "Sizeof CPU Config: " << sizeof(RISCVCPUConfig) << std::endl;
    std::cout << "Ext fields: " <<  &rv_cfg.rvv_ta_all_1s - &rv_cfg.ext_zba << std::endl;

    std::cout << "begin" << std::endl;
    while (ctx.pc_next < 72) {
        riscv_decode_insn(&ctx);
        std::cout << ctx.pc_next << std::endl;
    }
}