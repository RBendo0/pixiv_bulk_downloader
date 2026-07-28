#ifndef PBD_ENCODER_H
#define PBD_ENCODER_H

#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

/*
-----------------------------------------------------------------------
 Opaque encoder context

 The structure is defined internally. Callers only keep and pass
 the pointer returned by encoder_init().
-----------------------------------------------------------------------
*/

typedef struct EncoderContext EncoderContext;

/*
-----------------------------------------------------------------------
 Public API

 This module implements a streaming animation encoder.

 Typical usage:

     EncoderContext *ctx = encoder_init();

     encoder_start(ctx, ...);

     encoder_add_frame(ctx, ...);
     encoder_add_frame(ctx, ...);
     encoder_add_frame(ctx, ...);

     encoder_stop(ctx);
     encoder_destroy(ctx);

-----------------------------------------------------------------------
*/

/*
 * Allocates and initializes one independent encoder context.
 *
 * Returns NULL if memory allocation fails.
 */
EncoderContext *encoder_init(void);

/*
 * Starts a new encoding session.
 *
 * ctx
 *      Encoder context returned by encoder_init().
 *
 * output_file
 *      Destination file.
 *
 * format
 *      Container format.
 *      Examples:
 *          "webm"
 *          "mp4"
 *          "gif"
 *
 * codec
 *      FFmpeg encoder name.
 *      Examples:
 *          "libvpx-vp9"
 *          "libvpx"
 *          "libaom-av1"
 *          "libx264"
 *          "libx265"
 */
int encoder_start(EncoderContext *ctx, const char *output_file,
                  const char *format, const char *codec);

/*
 * Adds one compressed image frame.
 *
 * ctx
 *      Encoder context returned by encoder_init().
 *
 * data
 *      PNG/JPEG compressed bytes.
 *
 * size
 *      Number of bytes.
 *
 * duration_ms
 *      Frame duration in milliseconds.
 */
int encoder_add_frame(EncoderContext *ctx, const void *data, size_t size,
                      uint32_t duration_ms);

/*
 * Flushes the encoder, writes the trailer and closes the current
 * encoding session.
 */
int encoder_stop(EncoderContext *ctx);

/*
 * Releases any remaining FFmpeg resources and frees the encoder
 * context itself.
 *
 * This function may also be called after an interrupted or failed
 * encoding session.
 */
void encoder_destroy(EncoderContext *ctx);

#ifdef __cplusplus
}
#endif

#endif
