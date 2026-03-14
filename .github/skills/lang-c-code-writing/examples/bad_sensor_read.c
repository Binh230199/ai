/**
 * BAD EXAMPLE — violations annotated inline.
 * DO NOT use this pattern in production code.
 */

#include "sensor_driver.h"

/* BAD: global variable not static — pollutes external linkage (MISRA 8.7) */
int isInit = 0;

/* BAD: uses plain 'int' everywhere instead of fixed-width types (MISRA 10.1) */
int readTemp(int16_t *t)   /* BAD: return type 'int' has no semantic meaning */
{
    /* BAD: no NULL check on pointer 't' — undefined behaviour if caller passes NULL */

    /* BAD: magic numbers 3, 100, 4096 — undocumented, fragile (project rule) */
    *t = adc_read(3) * 100 / 4096;

    /* BAD: isInit used as integer in boolean context (MISRA 14.4) */
    if (isInit)
    {
        /* BAD: return value of adc_read() not stored — side-effect dependent */
    }

    /* BAD: raw integer 0 as error code; caller can't distinguish error types */
    return 0;
}

/* BAD: no module initialisation guard; no Doxygen comment */
void sensor_init()
{
    isInit = 1;   /* BAD: not atomic, not thread-safe, no documentation */
}

/* BAD: VLA — heap-like behaviour on stack, forbidden by MISRA C:2012 Rule 18.8 */
void process(int n)
{
    uint8_t buffer[n];   /* n is runtime value */
    /* ... */
}

/* BAD: strcpy without bounds — buffer overflow risk */
void copyName(char *dst, const char *src)
{
    strcpy(dst, src);   /* use strncpy(dst, src, DST_SIZE - 1U) instead */
}
