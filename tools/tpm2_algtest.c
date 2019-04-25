#include "options.h"
#include "util.h"
#include "scenario.h"
#include "logging.h"
#include "keygen.h"
#include "perf.h"

#include "tpm2_tool.h"
#include "tpm2_session.h"
#include "tpm2_options.h"
#include "tpm2_util.h"

#include <time.h>
#include <string.h>
#include <stdlib.h>
#include <sys/stat.h>
#include <limits.h>

struct tpm_algtest_options options = {
    .repetitions = 0,
    .max_duration_s = 0,
    .no_export = false,
    .scenario = "none",
    .command = "all",
    .type = "all",
    .algorithm = "all",
    .keylen = 0,
    .curveid = TPM2_ECC_NONE,
    .verbose = TPM2_ALGTEST_VERBOSE_INFO
};

static
bool on_option(char key, char *value)
{
    switch (key) {
    case 's':
        options.scenario = value;
        break;
    case 'd':
        options.max_duration_s = atoi(value);
        break;
    case 't':
        options.type = value;
        break;
    case 'c':
        options.command = value;
        break;
    case 'l':
        options.keylen = atoi(value);
        break;
    case 'C':
        options.curveid = strtol(value, NULL, 0);
        break;
    case 'n':
        options.repetitions = atoi(value);
        break;
    case 'a':
        options.algorithm = value;
        break;
    case 'x':
        options.no_export = true;
        break;
    }
    return true;
}

bool tpm2_tool_onstart(tpm2_options **opts)
{
    const struct option topts[] = {
        { "scenario", required_argument, NULL, 's' },
        { "duration", required_argument, NULL, 'd' },
        { "type", required_argument, NULL, 't' },
        { "command", required_argument, NULL, 'c' },
        { "keylen", required_argument, NULL, 'l' },
        { "curveid", required_argument, NULL, 'C' },
        { "algorithm", required_argument, NULL, 'a' },
        { "no_export", no_argument, NULL, 'x' },
    };
    *opts = tpm2_options_new("s:d:n:t:c:l:C:a:x", ARRAY_LEN(topts), topts, on_option, NULL, 0);

    return *opts != NULL;
}

int tpm2_tool_onrun(TSS2_SYS_CONTEXT *sapi_context, tpm2_option_flags flags)
{
    struct scenario_parameters parameters = {
        .repetitions = options.repetitions,
        .max_duration_s = options.max_duration_s,
    };
    set_default_parameters(&parameters, 1000, UINT_MAX);

    if (scenario_in_options("keygen")) {
        run_keygen_scenarios(sapi_context, &parameters);
    }

    if (scenario_in_options("perf")) {
        run_perf_scenarios(sapi_context, &parameters);
    }

    return 0;
}

