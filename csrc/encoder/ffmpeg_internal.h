#ifndef PBD_FFMPEG_INTERNAL_H
#define PBD_FFMPEG_INTERNAL_H

#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

/*
=====================================================================
    FFmpeg headers
=====================================================================
*/

#include <libavcodec/avcodec.h>
#include <libavfilter/avfilter.h>
#include <libavformat/avformat.h>
#include <libavutil/avutil.h>

#include <libavutil/imgutils.h>
#include <libavutil/rational.h>
#include <libswscale/swscale.h>

/*
=====================================================================
    Internal encoder context

    This structure contains the complete state of one encoding session.

    It is intentionally hidden from the public API.
=====================================================================
*/

typedef struct EncoderContext {
  /*
  -------------------------------------------------------------
      Output information
  -------------------------------------------------------------
  */

  char output_file[1024];

  char format_name[32];

  char codec_name[64];

  /*
  -------------------------------------------------------------
      Container
  -------------------------------------------------------------
  */

  AVFormatContext *format_ctx;

  AVStream *video_stream;

  /*
  -------------------------------------------------------------
      Video encoder
  -------------------------------------------------------------
  */

  const AVCodec *video_codec;

  AVCodecContext *video_encoder;

  /*
  -------------------------------------------------------------
      GIF filter graph

      The graph converts decoded image frames into PAL8 frames
      through FFmpeg's palettegen and paletteuse filters.

      These fields remain NULL for video encoders that do not
      require the GIF filtering pipeline.
  -------------------------------------------------------------
  */

  AVFilterGraph *filter_graph;

  AVFilterContext *buffersrc_ctx;

  AVFilterContext *buffersink_ctx;

  /*
  -------------------------------------------------------------
      Image decoder

      The codec is automatically detected from the first frame.
  -------------------------------------------------------------
  */

  enum AVCodecID image_codec_id;

  const AVCodec *image_codec;

  AVCodecContext *image_decoder;

  /*
  -------------------------------------------------------------
      Pixel format conversion
  -------------------------------------------------------------
  */

  struct SwsContext *sws;

  /*
  -------------------------------------------------------------
      Decoder packet
  -------------------------------------------------------------
  */

  AVPacket *decode_packet;

  /*
  -------------------------------------------------------------
      Encoder packet
  -------------------------------------------------------------
  */

  AVPacket *encode_packet;

  /*
  -------------------------------------------------------------
      Decoded image
  -------------------------------------------------------------
  */

  AVFrame *decoded_frame;

  /*
  -------------------------------------------------------------
      Frame passed to the video encoder
  -------------------------------------------------------------
  */

  AVFrame *encoder_frame;

  /*
  -------------------------------------------------------------
      Video properties

      Filled after decoding the first image.
  -------------------------------------------------------------
  */

  int width;

  int height;

  enum AVPixelFormat pixel_format;

  AVRational sample_aspect_ratio;

  enum AVColorSpace color_space;

  enum AVColorRange color_range;

  /*
  -------------------------------------------------------------
      Timing
  -------------------------------------------------------------
  */

  int64_t current_pts;

  int64_t current_time_ms;

  AVRational time_base;

  /*
  -------------------------------------------------------------
      Encoder state
  -------------------------------------------------------------
  */

  int initialized;

  int decoder_initialized;

  int frame_count;

} EncoderContext;

/*
=====================================================================
    Internal API
=====================================================================
*/

/*
 * Opens a new encoding session.
 */
int ffmpeg_encoder_open(EncoderContext *ctx, const char *output_file,
                        const char *format, const char *codec);

/*
 * Decodes one compressed image and encodes one video frame.
 */
int ffmpeg_encoder_add_frame(EncoderContext *ctx, const void *data, size_t size,
                             uint32_t duration_ms);

/*
 * Flushes encoder and releases every FFmpeg object.
 */
int ffmpeg_encoder_close(EncoderContext *ctx);

/*
=====================================================================
    Internal helper functions

    Used only inside ffmpeg_internal.c
=====================================================================
*/

int ffmpeg_open_container(EncoderContext *ctx);

int ffmpeg_open_image_decoder(EncoderContext *ctx, const void *data,
                              size_t size);

int ffmpeg_open_video_encoder(EncoderContext *ctx);

int ffmpeg_decode_image(EncoderContext *ctx, const void *data, size_t size);

int ffmpeg_encode_frame(EncoderContext *ctx);

int ffmpeg_flush_encoder(EncoderContext *ctx);

void ffmpeg_release(EncoderContext *ctx);

#ifdef __cplusplus
}
#endif

#endif