#include "encoder.h"

#include <stdlib.h>
#include <string.h>

#include "ffmpeg_internal.h"

/*--------------------------------------------------------------*/

EncoderContext *encoder_init(void) {
  EncoderContext *ctx;

  ctx = malloc(sizeof(*ctx));

  if (ctx == NULL) {
    return NULL;
  }

  memset(ctx, 0, sizeof(*ctx));

  return ctx;
}

/*--------------------------------------------------------------*/

int encoder_start(EncoderContext *ctx, const char *output_file,
                  const char *format, const char *codec,
                  const uint32_t *palette, size_t palette_size) {
  if (ctx == NULL) {
    return -1;
  }

  return ffmpeg_encoder_open(ctx, output_file, format, codec, palette,
                             palette_size);
}

/*--------------------------------------------------------------*/

int encoder_add_frame(EncoderContext *ctx, const void *data, size_t size,
                      uint32_t duration_ms) {
  if (ctx == NULL) {
    return -1;
  }

  return ffmpeg_encoder_add_frame(ctx, data, size, duration_ms);
}

/*--------------------------------------------------------------*/

int encoder_stop(EncoderContext *ctx) {
  if (ctx == NULL) {
    return -1;
  }

  return ffmpeg_encoder_close(ctx);
}

/*--------------------------------------------------------------*/

void encoder_destroy(EncoderContext *ctx) {
  if (ctx == NULL) {
    return;
  }

  /*
   * encoder_stop() normally releases these resources first.
   * Calling ffmpeg_release() here also covers failed or interrupted
   * sessions that never reached encoder_stop().
   */
  ffmpeg_release(ctx);

  memset(ctx, 0, sizeof(*ctx));

  free(ctx);
}
