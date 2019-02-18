#pragma once
#include <tss2/tss2_sys.h>
#include "create.h"

TPM2_RC test_parms(
        TSS2_SYS_CONTEXT *sapi_context,
        const TPMT_PUBLIC *publicArea);

TPM2B_PUBLIC prepare_template_RSA_primary(TPMI_RSA_KEY_BITS keyBits);
TPM2B_PUBLIC prepare_template_SYMCIPHER_primary();

TPM2B_PUBLIC prepare_template_RSA(TPMI_RSA_KEY_BITS keyBits);
TPM2B_PUBLIC prepare_template_ECC(TPMI_ECC_CURVE curveID);

TPM2_RC create_primary(
        TSS2_SYS_CONTEXT *sapi_context,
        const TPM2B_PUBLIC *inPublic,
        TPMI_DH_OBJECT *parent_handle);

TPM2_RC create(
        TSS2_SYS_CONTEXT *sapi_context,
        const TPM2B_PUBLIC *inPublic,
        TPMI_DH_OBJECT primary_handle,
        double *duration);