#ifndef TRANSLATE_H_
#define TRANSLATE_H_

typedef enum {
    MXL_RV32  = 1,
    MXL_RV64  = 2,
    MXL_RV128 = 3,
} RISCVMXL;

typedef struct {
    uint8_t ol;
    uint8_t xl;
    uint64_t misa_ext;
    uint32_t cur_insn_len;
    uint64_t pc_next;
    uint64_t base_off;
    RISCVCPUConfig *cfg_ptr;
} DisasContext;

/*
 * Consider updating misa_ext_info_arr[] and misa_ext_cfgs[]
 * when adding new MISA bits here.
 */
#define RV(x) ((uint64_t)1 << (x - 'A'))

#define RVI RV('I')
#define RVE RV('E') /* E and I are mutually exclusive */
#define RVM RV('M')
#define RVA RV('A')
#define RVF RV('F')
#define RVD RV('D')
#define RVV RV('V')
#define RVC RV('C')
#define RVS RV('S')
#define RVU RV('U')
#define RVH RV('H')
#define RVJ RV('J')
#define RVG RV('G')

void riscv_set_misa(DisasContext *ctx, uint64_t ext);
void riscv_decode_insn(DisasContext *ctx);

#endif