#include <stdint.h>
#include <stdbool.h>
#include <stdio.h>
#include "bitops.h"
#include "compiler.h"
#include "cpu_cfg.h"
#include "translate.h"

#define MAX_INSN_LEN 4
#define get_ol(ctx)  ((ctx)->ol)


void riscv_set_misa(DisasContext *ctx, uint64_t ext) {
    ctx->misa_ext |= ext;
}

static int ex_plus_1(DisasContext *ctx, int nf)
{
    return nf + 1;
}

#define EX_SH(amount) \
    static int ex_shift_##amount(DisasContext *ctx, int imm) \
    {                                         \
        return imm << amount;                 \
    }
EX_SH(1)
EX_SH(2)
EX_SH(3)
EX_SH(4)
EX_SH(12)

static int ex_rvc_register(DisasContext *ctx, int reg)
{
    return 8 + reg;
}

static int ex_sreg_register(DisasContext *ctx, int reg)
{
    return reg < 2 ? reg + 8 : reg + 16;
}

static int ex_rvc_shiftli(DisasContext *ctx, int imm)
{
    /* For RV128 a shamt of 0 means a shift by 64. */
    if (get_ol(ctx) == MXL_RV128) {
        imm = imm ? imm : 64;
    }
    return imm;
}

static int ex_rvc_shiftri(DisasContext *ctx, int imm)
{
    /*
     * For RV128 a shamt of 0 means a shift by 64, furthermore, for right
     * shifts, the shamt is sign-extended.
     */
    if (get_ol(ctx) == MXL_RV128) {
        imm = imm | (imm & 32) << 1;
        imm = imm ? imm : 64;
    }
    return imm;
}

#include "gen/riscv/decode-insn32.c.inc"
#include "gen/riscv/decode-insn16.c.inc"
#include "gen/riscv/decode-XVentanaCodeOps.c.inc"
#include "gen/riscv/decode-xthead.c.inc"

static inline int insn_len(uint16_t first_word) {
    return (first_word & 3) == 3 ? 4 : 2;
}

static inline bool has_ext(DisasContext *ctx, uint32_t ext) {
    return ctx->misa_ext & ext;
}

static uint32_t translator_lduw(uint64_t base, uint64_t offset) {
    return *((uint32_t *) (base + offset));
}

static void decode_opc(DisasContext *ctx, uint16_t opcode)
{
    /*
     * A table with predicate (i.e., guard) functions and decoder functions
     * that are tested in-order until a decoder matches onto the opcode.
     */
    static const struct {
        bool (*guard_func)(const RISCVCPUConfig *);
        bool (*decode_func)(DisasContext *, uint32_t);
    } decoders[] = {
        { always_true_p,  decode_insn32 },
        { has_xthead_p, decode_xthead },
        { has_XVentanaCondOps_p,  decode_XVentanaCodeOps },
    };

    ctx->cur_insn_len = insn_len(opcode);
    /* Check for compressed insn */
    if (ctx->cur_insn_len == 2) {
        /*
         * The Zca extension is added as way to refer to instructions in the C
         * extension that do not include the floating-point loads and stores
         */
        if ((has_ext(ctx, RVC) || ctx->cfg_ptr->ext_zca) &&
            decode_insn16(ctx, opcode)) {
            return;
        }
    } else {
        uint32_t opcode32 = opcode;
        opcode32 = deposit32(opcode32, 16, 16,
                             translator_lduw(ctx->base_off, ctx->pc_next + 2));

        for (size_t i = 0; i < ARRAY_SIZE(decoders); ++i) {
            if (decoders[i].guard_func(ctx->cfg_ptr) &&
                decoders[i].decode_func(ctx, opcode32)) {
                return;
            }
        }
    }
}


#ifdef ASMA_DEBUG
#include <stdio.h>
#endif

void riscv_decode_insn(DisasContext *ctx)
{
    #ifdef ASMA_DEBUG
        printf("data: %d \n", translator_lduw(ctx->base_off, ctx->pc_next));
        printf("ctx: xl %d\n", ctx->xl);
        printf("ctx: ol %d\n", ctx->ol);
        printf("ctx: pc_next %ld\n", ctx->pc_next);
        printf("ctx: base_off %ld\n", ctx->base_off);
        printf("ctx: cfg_ptr %ld\n", (uint64_t) ctx->cfg_ptr);
    #endif
    uint16_t opcode16 = translator_lduw(ctx->base_off, ctx->pc_next);
    ctx->ol = ctx->xl;
    decode_opc(ctx, opcode16);
    ctx->pc_next += ctx->cur_insn_len;
}
