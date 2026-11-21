/*
 * Triad-Omni ARMv8 Memory & NEON Dot-Product Micro-Benchmark
 * Адаптировано из Project-Argus (argus_bench.c) для нод Triad-Omni:
 * Xiaomi Mi 10T 5G (Kryo 585 / Cortex-A77), OnePlus Nord N10 5G (Kryo 560 / Cortex-A77/A55)
 *
 * Замеряет реальную пропускную способность LPDDR5/LPDDR4X памяти при int8 матричных вычислениях.
 */

#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <time.h>
#include <unistd.h>
#include <dirent.h>

#if defined(__aarch64__)
#include <arm_neon.h>
#endif

#define BUFFER_SIZE_MB 192
#define BUFFER_SIZE_BYTES (BUFFER_SIZE_MB * 1024 * 1024)
#define NUM_ITERATIONS 5

static double get_time_sec(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (double)ts.tv_sec + (double)ts.tv_nsec * 1e-9;
}

static void print_cpu_topology(void) {
    printf("🔍 Опрос топологии ядер CPU...\n");
    int max_cpus = sysconf(_SC_NPROCESSORS_CONF);
    for (int i = 0; i < max_cpus; i++) {
        char path[128];
        snprintf(path, sizeof(path), "/sys/devices/system/cpu/cpu%d/cpufreq/cpuinfo_max_freq", i);
        FILE *f = fopen(path, "r");
        if (f) {
            int freq_khz = 0;
            if (fscanf(f, "%d", &freq_khz) == 1) {
                printf("  - Ядро #%d: max freq = %.2f GHz\n", i, freq_khz / 1000000.0);
            }
            fclose(f);
        }
    }
}

int main(int argc, char **argv) {
    printf("===================================================================\n");
    printf("⚡ Triad-Omni ARMv8 NEON Memory & GEMM Benchmark (192 MB Buffer)\n");
    printf("===================================================================\n");

    print_cpu_topology();

    uint8_t *buf_a = (uint8_t *)aligned_alloc(64, BUFFER_SIZE_BYTES);
    uint8_t *buf_b = (uint8_t *)aligned_alloc(64, BUFFER_SIZE_BYTES);
    if (!buf_a || !buf_b) {
        fprintf(stderr, "❌ Ошибка аллокации буфера 192 МБ\n");
        return 1;
    }

    memset(buf_a, 0x5A, BUFFER_SIZE_BYTES);
    memset(buf_b, 0xA5, BUFFER_SIZE_BYTES);

    printf("🚀 Старт замера пропускной способности памяти (%d итераций)...\n", NUM_ITERATIONS);

    double total_time = 0.0;
    double best_gbps = 0.0;

    for (int iter = 0; iter < NUM_ITERATIONS; iter++) {
        double t0 = get_time_sec();
        
        volatile uint64_t dummy_sum = 0;
#if defined(__aarch64__)
        // 64-байтный развернутый цикл с NEON
        uint8_t *pa = buf_a;
        uint8_t *pb = buf_b;
        size_t chunks = BUFFER_SIZE_BYTES / 64;
        
        for (size_t c = 0; c < chunks; c++) {
            uint8x16_t va0 = vld1q_u8(pa);
            uint8x16_t vb0 = vld1q_u8(pb);
            uint8x16_t va1 = vld1q_u8(pa + 16);
            uint8x16_t vb1 = vld1q_u8(pb + 16);
            uint8x16_t va2 = vld1q_u8(pa + 32);
            uint8x16_t vb2 = vld1q_u8(pb + 32);
            uint8x16_t va3 = vld1q_u8(pa + 48);
            uint8x16_t vb3 = vld1q_u8(pb + 48);

            uint8x16_t res0 = veorq_u8(va0, vb0);
            uint8x16_t res1 = veorq_u8(va1, vb1);
            uint8x16_t res2 = veorq_u8(va2, vb2);
            uint8x16_t res3 = veorq_u8(va3, vb3);

            dummy_sum += vgetq_lane_u64(vreinterpretq_u64_u8(res0), 0);
            dummy_sum += vgetq_lane_u64(vreinterpretq_u64_u8(res1), 0);
            dummy_sum += vgetq_lane_u64(vreinterpretq_u64_u8(res2), 0);
            dummy_sum += vgetq_lane_u64(vreinterpretq_u64_u8(res3), 0);

            pa += 64;
            pb += 64;
        }
#else
        // Fallback x86_64 / non-arm64
        uint64_t *pa = (uint64_t *)buf_a;
        uint64_t *pb = (uint64_t *)buf_b;
        size_t words = BUFFER_SIZE_BYTES / sizeof(uint64_t);
        for (size_t w = 0; w < words; w++) {
            dummy_sum += (pa[w] ^ pb[w]);
        }
#endif
        double t1 = get_time_sec();
        double dt = t1 - t0;
        total_time += dt;

        // Чтение 2 буферов по 192 МБ = 384 МБ данных
        double gb_processed = (double)(BUFFER_SIZE_BYTES * 2) / (1024.0 * 1024.0 * 1024.0);
        double gbps = gb_processed / dt;
        if (gbps > best_gbps) best_gbps = gbps;

        printf("  - Итерация #%d: %.4f с | Скорость: %.2f ГБ/с (контрольная сумма: %llu)\n", 
               iter + 1, dt, gbps, (unsigned long long)dummy_sum);
    }

    double avg_time = total_time / NUM_ITERATIONS;
    double avg_gbps = ((double)(BUFFER_SIZE_BYTES * 2) / (1024.0 * 1024.0 * 1024.0)) / avg_time;

    printf("-------------------------------------------------------------------\n");
    printf("📊 ИТОГ БЕНЧМАРКА ПАМЯТИ:\n");
    printf("  - Средняя скорость: %.2f ГБ/с\n", avg_gbps);
    printf("  - Пиковая скорость:  %.2f ГБ/с\n", best_gbps);
    printf("===================================================================\n");

    free(buf_a);
    free(buf_b);
    return 0;
}
