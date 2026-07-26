/*
=====================================================================

    PBD native encoder benchmark

    Expected dataset:

      C:\Users\pc\pbd\test
      ├── 1
      │   ├── metadata.csv
      │   ├── 000000.jpg
      │   └── ...
      ├── 2
      └── ...

    metadata.csv format (no header):

      000000.jpg,100
      000001.jpg,60

=====================================================================
*/

#include <ctype.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <windows.h>

#include "../encoder.h"

#define TEST_ROOT "C:\\Users\\pc\\pbd\\test"
#define FIRST_TEST 1
#define LAST_TEST 12

#define METADATA_NAME "metadata.csv"
#define RESULTS_NAME "benchmark.csv"

#define PATH_BUFFER_SIZE 1024
#define LINE_BUFFER_SIZE 1024
#define FRAME_NAME_SIZE 512

typedef struct BenchmarkProfile {
  const char *name;
  const char *output_name;
  const char *container_name;
  const char *codec_name;
} BenchmarkProfile;

static const BenchmarkProfile BENCHMARK_PROFILES[] = {
    {"webm", "output.webm", "webm", "libvpx-vp9"},
    {"mp4", "output.mp4", "mp4", "libx264"},
    {"gif-default", "output.gif", "gif", "gif"},
};

#define BENCHMARK_PROFILE_COUNT                                                \
  (sizeof(BENCHMARK_PROFILES) / sizeof(BENCHMARK_PROFILES[0]))

/*
---------------------------------------------------------------------
    Reads an entire file into memory.
---------------------------------------------------------------------
*/

static int read_file(const char *filename, void **buffer, size_t *size) {
  FILE *fp;
  long length;
  void *memory;

  if (filename == NULL || buffer == NULL || size == NULL) {
    return 0;
  }

  *buffer = NULL;
  *size = 0;

  fp = fopen(filename, "rb");

  if (fp == NULL) {
    return 0;
  }

  if (fseek(fp, 0, SEEK_END) != 0) {
    fclose(fp);
    return 0;
  }

  length = ftell(fp);

  if (length <= 0) {
    fclose(fp);
    return 0;
  }

  rewind(fp);

  memory = malloc((size_t)length);

  if (memory == NULL) {
    fclose(fp);
    return 0;
  }

  if (fread(memory, 1, (size_t)length, fp) != (size_t)length) {
    free(memory);
    fclose(fp);
    return 0;
  }

  fclose(fp);

  *buffer = memory;
  *size = (size_t)length;

  return 1;
}

/*
---------------------------------------------------------------------
    Releases a previously loaded frame.
---------------------------------------------------------------------
*/

static void release_frame(void *buffer) { free(buffer); }

/*
---------------------------------------------------------------------
    Builds a path and reports truncation.
---------------------------------------------------------------------
*/

static int make_path(char *destination, size_t capacity, const char *format,
                     int test_number, const char *filename) {
  int written;

  if (destination == NULL || capacity == 0 || format == NULL) {
    return 0;
  }

  written =
      snprintf(destination, capacity, format, TEST_ROOT, test_number, filename);

  return written >= 0 && (size_t)written < capacity;
}

/*
---------------------------------------------------------------------
    Removes trailing newline characters and surrounding whitespace.
---------------------------------------------------------------------
*/

static void trim_line(char *text) {
  char *start;
  char *end;

  if (text == NULL) {
    return;
  }

  start = text;

  while (*start != '\0' && isspace((unsigned char)*start)) {
    ++start;
  }

  if (start != text) {
    memmove(text, start, strlen(start) + 1);
  }

  end = text + strlen(text);

  while (end > text && isspace((unsigned char)end[-1])) {
    --end;
  }

  *end = '\0';
}

/*
---------------------------------------------------------------------
    Reads one "filename,delay" record.

    Returns:
      1  valid record
      0  blank line
     -1  malformed record
---------------------------------------------------------------------
*/

static int parse_frame_record(char *line, char *filename,
                              size_t filename_capacity, int *delay_ms) {
  char *comma;
  char *delay_text;
  char *end;
  long delay;

  if (line == NULL || filename == NULL || filename_capacity == 0 ||
      delay_ms == NULL) {
    return -1;
  }

  trim_line(line);

  if (line[0] == '\0') {
    return 0;
  }

  comma = strchr(line, ',');

  if (comma == NULL || strchr(comma + 1, ',') != NULL) {
    return -1;
  }

  *comma = '\0';
  delay_text = comma + 1;

  trim_line(line);
  trim_line(delay_text);

  if (line[0] == '\0' || delay_text[0] == '\0' ||
      strlen(line) >= filename_capacity) {
    return -1;
  }

  delay = strtol(delay_text, &end, 10);

  while (*end != '\0' && isspace((unsigned char)*end)) {
    ++end;
  }

  if (*end != '\0' || delay <= 0 || delay > 2147483647L) {
    return -1;
  }

  strcpy(filename, line);
  *delay_ms = (int)delay;

  return 1;
}

/*
---------------------------------------------------------------------
    Encodes one test directory.
---------------------------------------------------------------------
*/

static int encode_test(int test_number, const BenchmarkProfile *profile,
                       size_t *encoded_frames, unsigned long long *elapsed_ms) {
  char metadata_path[PATH_BUFFER_SIZE];
  char output_path[PATH_BUFFER_SIZE];
  char frame_path[PATH_BUFFER_SIZE];
  char line[LINE_BUFFER_SIZE];
  char frame_name[FRAME_NAME_SIZE];

  FILE *metadata;

  EncoderContext *ctx = NULL;

  size_t line_number;
  size_t frame_count;

  unsigned long long start_time;

  int encoder_started;
  int result;

  if (profile == NULL || encoded_frames == NULL || elapsed_ms == NULL) {
    return 0;
  }

  *encoded_frames = 0;
  *elapsed_ms = 0;

  if (!make_path(metadata_path, sizeof(metadata_path), "%s\\%d\\%s",
                 test_number, METADATA_NAME) ||
      !make_path(output_path, sizeof(output_path), "%s\\%d\\%s", test_number,
                 profile->output_name)) {
    printf("[ERRORE] Test %d: percorso troppo lungo.\n", test_number);
    return 0;
  }

  metadata = fopen(metadata_path, "r");

  if (metadata == NULL) {
    printf("[ERRORE] Test %d: impossibile aprire %s\n", test_number,
           metadata_path);
    return 0;
  }

  printf("\n[Test %d - %s]\n", test_number, profile->name);
  printf("Metadata:  %s\n", metadata_path);
  printf("Output:    %s\n", output_path);
  printf("Container: %s\n", profile->container_name);
  printf("Codec:     %s\n", profile->codec_name);

  start_time = GetTickCount64();
  encoder_started = 0;
  result = 0;
  line_number = 0;
  frame_count = 0;

  ctx = encoder_init();

  if (ctx == NULL) {
    printf("[ERRORE] Test %d: impossibile creare il contesto encoder.\n",
           test_number);
    goto cleanup;
  }

  if (encoder_start(ctx, output_path, profile->container_name,
                    profile->codec_name) != 0) {
    printf("[ERRORE] Test %d - %s: inizializzazione encoder fallita.\n",
           test_number, profile->name);
    goto cleanup;
  }

  encoder_started = 1;

  while (fgets(line, sizeof(line), metadata) != NULL) {
    void *buffer;
    size_t size;
    int delay_ms;
    int parse_result;

    ++line_number;

    if (strchr(line, '\n') == NULL && !feof(metadata)) {
      printf("[ERRORE] Test %d, riga %zu: riga troppo lunga.\n", test_number,
             line_number);
      goto cleanup;
    }

    parse_result =
        parse_frame_record(line, frame_name, sizeof(frame_name), &delay_ms);

    if (parse_result == 0) {
      continue;
    }

    if (parse_result < 0) {
      printf("[ERRORE] Test %d, riga %zu: record CSV non valido.\n",
             test_number, line_number);
      goto cleanup;
    }

    if (!make_path(frame_path, sizeof(frame_path), "%s\\%d\\%s", test_number,
                   frame_name)) {
      printf("[ERRORE] Test %d, riga %zu: percorso frame troppo lungo.\n",
             test_number, line_number);
      goto cleanup;
    }

    buffer = NULL;
    size = 0;

    if (!read_file(frame_path, &buffer, &size)) {
      printf("[ERRORE] Test %d, riga %zu: impossibile leggere %s\n",
             test_number, line_number, frame_path);
      goto cleanup;
    }

    if (encoder_add_frame(ctx, buffer, size, delay_ms) != 0) {
      printf("[ERRORE] Test %d, riga %zu: codifica fallita per %s\n",
             test_number, line_number, frame_name);
      release_frame(buffer);
      goto cleanup;
    }

    release_frame(buffer);

    ++frame_count;

    printf("\rFrame codificati: %zu", frame_count);
    fflush(stdout);
  }

  if (ferror(metadata)) {
    printf("\n[ERRORE] Test %d: errore durante la lettura del CSV.\n",
           test_number);
    goto cleanup;
  }

  if (frame_count == 0) {
    printf("\n[ERRORE] Test %d: nessun frame trovato.\n", test_number);
    goto cleanup;
  }

  if (encoder_stop(ctx) != 0) {
    encoder_started = 0;
    printf("\n[ERRORE] Test %d: finalizzazione video fallita.\n", test_number);
    goto cleanup;
  }

  encoder_started = 0;

  *elapsed_ms = GetTickCount64() - start_time;
  *encoded_frames = frame_count;

  printf("\n[OK] %zu frame codificati in %.3f secondi.\n", frame_count,
         (double)*elapsed_ms / 1000.0);

  result = 1;

cleanup:
  if (encoder_started) {
    encoder_stop(ctx);
  }

  if (ctx != NULL) {
    encoder_destroy(ctx);
  }

  fclose(metadata);

  return result;
}

/*
---------------------------------------------------------------------
    Opens the benchmark result file and writes its header.
---------------------------------------------------------------------
*/

static FILE *open_results_file(void) {
  char results_path[PATH_BUFFER_SIZE];
  int written;
  FILE *results;

  written = snprintf(results_path, sizeof(results_path), "%s\\%s", TEST_ROOT,
                     RESULTS_NAME);

  if (written < 0 || (size_t)written >= sizeof(results_path)) {
    printf("[ERRORE] Percorso del file risultati troppo lungo.\n");
    return NULL;
  }

  results = fopen(results_path, "w");

  if (results == NULL) {
    printf("[ERRORE] Impossibile creare %s\n", results_path);
    return NULL;
  }

  fprintf(results, "test,profile,container,codec,frames,elapsed_ms,"
                   "elapsed_seconds,frames_per_second,status\n");

  printf("Risultati: %s\n", results_path);

  return results;
}

/*
=====================================================================
    Main
=====================================================================
*/

int main(void) {
  FILE *results;

  int test_number;
  int successful_tests;
  int failed_tests;

  printf("PBD native encoder benchmark\n");
  printf("Dataset: %s\n", TEST_ROOT);
  printf("Profili: %zu\n\n", (size_t)BENCHMARK_PROFILE_COUNT);

  for (size_t profile_index = 0; profile_index < BENCHMARK_PROFILE_COUNT;
       ++profile_index) {
    const BenchmarkProfile *profile = &BENCHMARK_PROFILES[profile_index];

    printf("  %-12s container=%-5s codec=%s\n", profile->name,
           profile->container_name, profile->codec_name);
  }

  printf("\n");

  results = open_results_file();

  if (results == NULL) {
    return EXIT_FAILURE;
  }

  successful_tests = 0;
  failed_tests = 0;

  for (test_number = FIRST_TEST; test_number <= LAST_TEST; ++test_number) {
    for (size_t profile_index = 0; profile_index < BENCHMARK_PROFILE_COUNT;
         ++profile_index) {
      const BenchmarkProfile *profile = &BENCHMARK_PROFILES[profile_index];

      size_t frame_count;
      unsigned long long elapsed_ms;
      int success;
      double elapsed_seconds;
      double frames_per_second;

      success = encode_test(test_number, profile, &frame_count, &elapsed_ms);

      elapsed_seconds = (double)elapsed_ms / 1000.0;

      frames_per_second =
          elapsed_ms > 0 ? ((double)frame_count * 1000.0) / (double)elapsed_ms
                         : 0.0;

      fprintf(results, "%d,%s,%s,%s,%zu,%llu,%.6f,%.3f,%s\n", test_number,
              profile->name, profile->container_name, profile->codec_name,
              frame_count, elapsed_ms, elapsed_seconds, frames_per_second,
              success ? "ok" : "error");

      fflush(results);

      if (success) {
        ++successful_tests;
      } else {
        ++failed_tests;
      }
    }
  }

  fclose(results);

  printf("\n========================================\n");
  printf("Codifiche completate: %d\n", successful_tests);
  printf("Codifiche fallite:    %d\n", failed_tests);
  printf("========================================\n");

  return failed_tests == 0 ? EXIT_SUCCESS : EXIT_FAILURE;
}