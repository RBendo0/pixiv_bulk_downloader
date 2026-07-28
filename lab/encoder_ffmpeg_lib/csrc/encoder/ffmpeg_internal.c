/*
=====================================================================

    Pixiv Bulk Downloader
    Native FFmpeg encoder

=====================================================================
*/

#include "ffmpeg_internal.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include <libavutil/mem.h>
#include <libavutil/opt.h>
#include <libavutil/pixdesc.h>

#include <libavfilter/buffersink.h>
#include <libavfilter/buffersrc.h>

/*
=====================================================================
    Internal constants
=====================================================================
*/

#define PBD_SUCCESS 0
#define PBD_ERROR -1

/*
=====================================================================
    Internal helper functions
=====================================================================
*/

static int ffmpeg_open_gif_filter_graph(EncoderContext *ctx);
static int ffmpeg_flush_gif_filter_graph(EncoderContext *ctx);
static int ffmpeg_create_sws_context(EncoderContext *ctx);
static int ffmpeg_prepare_video_frame(EncoderContext *ctx);
static int ffmpeg_prepare_encoder_frame(EncoderContext *ctx);
static void ffmpeg_normalize_decoded_frame(AVFrame *frame);

/*
 * Safely copies a C string into a fixed-size destination buffer.
 */
static void copy_string(char *destination, size_t destination_size,
                        const char *source) {
  if (destination == NULL || destination_size == 0) {
    return;
  }

  if (source == NULL) {
    destination[0] = '\0';
    return;
  }

  snprintf(destination, destination_size, "%s", source);
}

/*
 * Prints all AVOptions exposed by an FFmpeg object.
 */
static void ffmpeg_dump_avoptions(const char *section, void *object,
                                  int option_flags) {
  char *serialized_options = NULL;
  int result;

  fprintf(stderr, "\n[%s]\n", section);

  if (object == NULL) {
    fprintf(stderr, "(none)\n");
    return;
  }

  result =
      av_opt_serialize(object, option_flags, 0, &serialized_options, '=', '\n');

  if (result < 0 || serialized_options == NULL) {
    fprintf(stderr, "(unable to serialize options)\n");
    av_free(serialized_options);
    return;
  }

  fprintf(stderr, "%s\n", serialized_options);

  av_free(serialized_options);
}

/*
 * Prints the effective encoder and muxer configuration after FFmpeg
 * has opened the encoder and initialized the output container.
 */
static void ffmpeg_dump_encoder_configuration(const EncoderContext *ctx) {
  const char *pixel_format_name;

  if (ctx == NULL || ctx->video_encoder == NULL || ctx->format_ctx == NULL ||
      ctx->video_stream == NULL) {
    return;
  }

  pixel_format_name = av_get_pix_fmt_name(ctx->video_encoder->pix_fmt);

  fprintf(stderr,
          "\n"
          "============================================================\n"
          "FFMPEG LIBRARY CONFIGURATION\n"
          "============================================================\n"
          "output_file=%s\n"
          "container=%s\n"
          "codec=%s\n"
          "codec_id=%d\n"
          "width=%d\n"
          "height=%d\n"
          "pixel_format=%s\n"
          "time_base=%d/%d\n"
          "stream_time_base=%d/%d\n"
          "framerate=%d/%d\n"
          "bit_rate=%lld\n"
          "rc_min_rate=%lld\n"
          "rc_max_rate=%lld\n"
          "rc_buffer_size=%d\n"
          "gop_size=%d\n"
          "max_b_frames=%d\n"
          "thread_count=%d\n"
          "thread_type=%d\n"
          "profile=%d\n"
          "level=%d\n"
          "sample_aspect_ratio=%d/%d\n"
          "color_range=%d\n"
          "color_primaries=%d\n"
          "color_transfer=%d\n"
          "color_space=%d\n"
          "chroma_location=%d\n"
          "codec_flags=%d\n"
          "format_flags=%d\n",
          ctx->output_file, ctx->format_name, ctx->codec_name,
          ctx->video_encoder->codec_id, ctx->video_encoder->width,
          ctx->video_encoder->height,
          pixel_format_name != NULL ? pixel_format_name : "unknown",
          ctx->video_encoder->time_base.num, ctx->video_encoder->time_base.den,
          ctx->video_stream->time_base.num, ctx->video_stream->time_base.den,
          ctx->video_encoder->framerate.num, ctx->video_encoder->framerate.den,
          (long long)ctx->video_encoder->bit_rate,
          (long long)ctx->video_encoder->rc_min_rate,
          (long long)ctx->video_encoder->rc_max_rate,
          ctx->video_encoder->rc_buffer_size, ctx->video_encoder->gop_size,
          ctx->video_encoder->max_b_frames, ctx->video_encoder->thread_count,
          ctx->video_encoder->thread_type, ctx->video_encoder->profile,
          ctx->video_encoder->level,
          ctx->video_encoder->sample_aspect_ratio.num,
          ctx->video_encoder->sample_aspect_ratio.den,
          ctx->video_encoder->color_range, ctx->video_encoder->color_primaries,
          ctx->video_encoder->color_trc, ctx->video_encoder->colorspace,
          ctx->video_encoder->chroma_sample_location, ctx->video_encoder->flags,
          ctx->format_ctx->oformat->flags);

  ffmpeg_dump_avoptions("ENCODER PRIVATE OPTIONS",
                        ctx->video_encoder->priv_data,
                        AV_OPT_FLAG_ENCODING_PARAM | AV_OPT_FLAG_VIDEO_PARAM);

  ffmpeg_dump_avoptions("MUXER PRIVATE OPTIONS", ctx->format_ctx->priv_data,
                        AV_OPT_FLAG_ENCODING_PARAM);

  fprintf(stderr,
          "============================================================\n\n");
}

/*
 * Configures the output pixel format and the private options required
 * by the selected video encoder.
 */
static int ffmpeg_configure_video_encoder(EncoderContext *ctx) {
  int result;

  if (ctx == NULL || ctx->video_encoder == NULL) {
    return PBD_ERROR;
  }

  if (strcmp(ctx->codec_name, "gif") == 0) {
    ctx->video_encoder->pix_fmt = AV_PIX_FMT_PAL8;

    return PBD_SUCCESS;
  }

  if (strcmp(ctx->codec_name, "libvpx") == 0 ||
      strcmp(ctx->codec_name, "libvpx-vp9") == 0 ||
      strcmp(ctx->codec_name, "libaom-av1") == 0) {
    ctx->video_encoder->pix_fmt = AV_PIX_FMT_YUV420P;

    result = av_opt_set_int(ctx->video_encoder->priv_data, "crf", 30, 0);

    if (result < 0) {
      return PBD_ERROR;
    }

    return PBD_SUCCESS;
  }

  if (strcmp(ctx->codec_name, "libx264") == 0) {
    ctx->video_encoder->pix_fmt = AV_PIX_FMT_YUV420P;

    result = av_opt_set_int(ctx->video_encoder->priv_data, "crf", 23, 0);

    if (result < 0) {
      return PBD_ERROR;
    }

    result = av_opt_set(ctx->video_encoder->priv_data, "preset", "medium", 0);

    if (result < 0) {
      return PBD_ERROR;
    }

    return PBD_SUCCESS;
  }

  if (strcmp(ctx->codec_name, "libx265") == 0) {
    ctx->video_encoder->pix_fmt = AV_PIX_FMT_YUV420P;

    result = av_opt_set_int(ctx->video_encoder->priv_data, "crf", 28, 0);

    if (result < 0) {
      return PBD_ERROR;
    }

    result = av_opt_set(ctx->video_encoder->priv_data, "preset", "medium", 0);

    if (result < 0) {
      return PBD_ERROR;
    }

    return PBD_SUCCESS;
  }

  fprintf(stderr, "Unsupported encoder configuration: '%s'\n", ctx->codec_name);

  return PBD_ERROR;
}

/*
=====================================================================
    Public internal API
=====================================================================
*/

/*
 * Initializes one encoding session.
 */
int ffmpeg_encoder_open(EncoderContext *ctx, const char *output_file,
                        const char *format, const char *codec) {

  if (ctx == NULL) {
    return PBD_ERROR;
  }

  memset(ctx, 0, sizeof(*ctx));

  copy_string(ctx->output_file, sizeof(ctx->output_file), output_file);

  copy_string(ctx->format_name, sizeof(ctx->format_name), format);

  copy_string(ctx->codec_name, sizeof(ctx->codec_name), codec);

  ctx->time_base.num = 1;
  ctx->time_base.den = 1000;

  ctx->current_pts = 0;
  ctx->current_time_ms = 0;

  ctx->frame_count = 0;

  ctx->initialized = 0;
  ctx->decoder_initialized = 0;

  if (ffmpeg_open_container(ctx) != PBD_SUCCESS) {
    ffmpeg_release(ctx);

    return PBD_ERROR;
  }

  ctx->initialized = 1;

  return PBD_SUCCESS;
}

/*
 * Decodes and submits one compressed image frame to the selected
 * encoding pipeline.
 */
int ffmpeg_encoder_add_frame(EncoderContext *ctx, const void *data, size_t size,
                             uint32_t duration_ms) {
  int result;

  if (ctx == NULL || data == NULL || size == 0 || duration_ms == 0) {
    return PBD_ERROR;
  }

  result = ffmpeg_decode_image(ctx, data, size);

  if (result != PBD_SUCCESS) {
    return result;
  }

  if (strcmp(ctx->codec_name, "gif") == 0) {
    if (ctx->filter_graph == NULL) {
      result = ffmpeg_open_gif_filter_graph(ctx);

      if (result != PBD_SUCCESS) {
        return result;
      }
    }

    ctx->decoded_frame->pts = ctx->current_pts;

    result = av_buffersrc_add_frame_flags(
        ctx->buffersrc_ctx, ctx->decoded_frame, AV_BUFFERSRC_FLAG_KEEP_REF);

    if (result < 0) {
      return PBD_ERROR;
    }

    ctx->current_pts += duration_ms;
    ctx->current_time_ms += duration_ms;
    ++ctx->frame_count;

    return PBD_SUCCESS;
  }

  result = ffmpeg_prepare_encoder_frame(ctx);

  if (result != PBD_SUCCESS) {
    return result;
  }

  ctx->encoder_frame->pts = ctx->current_pts;

  result = ffmpeg_encode_frame(ctx);

  if (result != PBD_SUCCESS) {
    return result;
  }

  ctx->current_pts += duration_ms;
  ctx->current_time_ms += duration_ms;
  ++ctx->frame_count;

  return PBD_SUCCESS;
}

/*
=====================================================================
    Container initialization
=====================================================================
*/

/*
 * Creates the output container and prepares it for writing.
 */
int ffmpeg_open_container(EncoderContext *ctx) {
  int result;

  if (ctx == NULL) {
    return PBD_ERROR;
  }

  /*
  -------------------------------------------------------------
      Allocate the output format context.

      The format is selected from the string provided by Python
      (for example "webm" or "mp4").
  -------------------------------------------------------------
  */

  result = avformat_alloc_output_context2(&ctx->format_ctx, NULL,
                                          ctx->format_name, ctx->output_file);

  if (result < 0 || ctx->format_ctx == NULL) {
    return PBD_ERROR;
  }

  /*
  -------------------------------------------------------------
      Open the destination file when required.

      Some formats (memory streams, custom IO...) do not require
      an AVIOContext, therefore we first check the format flags.
  -------------------------------------------------------------
  */

  if (!(ctx->format_ctx->oformat->flags & AVFMT_NOFILE)) {
    result = avio_open(&ctx->format_ctx->pb, ctx->output_file, AVIO_FLAG_WRITE);

    if (result < 0) {
      ffmpeg_release(ctx);

      return PBD_ERROR;
    }
  }

  /*
  -------------------------------------------------------------
      Locate the requested video encoder.

      The codec name comes directly from the configuration
      generated by Python.
  -------------------------------------------------------------
  */

  ctx->video_codec = avcodec_find_encoder_by_name(ctx->codec_name);

  if (ctx->video_codec == NULL) {
    fprintf(stderr, "Unable to find encoder '%s'\n", ctx->codec_name);

    ffmpeg_release(ctx);

    return PBD_ERROR;
  }

  /*
  -------------------------------------------------------------
      Create the output video stream.

      The codec context will be created later, after decoding the
      first image, because only then width, height and pixel format
      are known.
  -------------------------------------------------------------
  */

  ctx->video_stream = avformat_new_stream(ctx->format_ctx, NULL);

  if (ctx->video_stream == NULL) {
    ffmpeg_release(ctx);

    return PBD_ERROR;
  }

  /*
  -------------------------------------------------------------
      Allocate reusable packets.

      Decoder and encoder intentionally use different packet
      instances.
  -------------------------------------------------------------
  */

  ctx->decode_packet = av_packet_alloc();

  ctx->encode_packet = av_packet_alloc();

  if (ctx->decode_packet == NULL || ctx->encode_packet == NULL) {
    ffmpeg_release(ctx);

    return PBD_ERROR;
  }

  /*
  -------------------------------------------------------------
      Allocate reusable frames.

      decoded_frame  -> output of the image decoder

      encoder_frame  -> input of the video encoder
  -------------------------------------------------------------
  */

  ctx->decoded_frame = av_frame_alloc();

  ctx->encoder_frame = av_frame_alloc();

  if (ctx->decoded_frame == NULL || ctx->encoder_frame == NULL) {
    ffmpeg_release(ctx);

    return PBD_ERROR;
  }

  return PBD_SUCCESS;
}

/*
=====================================================================
    Image decoder initialization
=====================================================================
*/

/*
 * Detects the image codec from the first compressed frame and
 * initializes the decoder.
 */
int ffmpeg_open_image_decoder(EncoderContext *ctx, const void *data,
                              size_t size) {
  AVProbeData probe;

  int result;

  if (ctx == NULL || data == NULL || size == 0) {
    return PBD_ERROR;
  }

  /*
  -------------------------------------------------------------
      Skip initialization if already completed.
  -------------------------------------------------------------
  */

  if (ctx->decoder_initialized) {
    return PBD_SUCCESS;
  }

  /*
  -------------------------------------------------------------
      Probe the compressed image.

      FFmpeg inspects the first bytes of the buffer and returns
      the most probable input format.
  -------------------------------------------------------------
  */

  memset(&probe, 0, sizeof(probe));

  probe.buf = (unsigned char *)data;
  probe.buf_size = (int)size;
  probe.filename = "";

  const AVInputFormat *input_format = av_probe_input_format(&probe, 1);

  if (input_format == NULL) {
    return PBD_ERROR;
  }

  /*
  -------------------------------------------------------------
      Determine the decoder to use.

      Currently we support the image codecs handled by FFmpeg.
      The actual codec id is inferred from the detected format.
  -------------------------------------------------------------
  */

  if (strcmp(input_format->name, "png_pipe") == 0 ||
      strcmp(input_format->name, "apng") == 0) {
    ctx->image_codec_id = AV_CODEC_ID_PNG;
  } else if (strcmp(input_format->name, "jpeg_pipe") == 0 ||
             strcmp(input_format->name, "mjpeg") == 0) {
    ctx->image_codec_id = AV_CODEC_ID_MJPEG;
  } else if (strcmp(input_format->name, "bmp_pipe") == 0) {
    ctx->image_codec_id = AV_CODEC_ID_BMP;
  } else if (strcmp(input_format->name, "webp_pipe") == 0) {
    ctx->image_codec_id = AV_CODEC_ID_WEBP;
  } else {
    return PBD_ERROR;
  }

  /*
  -------------------------------------------------------------
      Locate the decoder.
  -------------------------------------------------------------
  */

  ctx->image_codec = avcodec_find_decoder(ctx->image_codec_id);

  if (ctx->image_codec == NULL) {
    return PBD_ERROR;
  }

  /*
  -------------------------------------------------------------
      Allocate the decoder context.
  -------------------------------------------------------------
  */

  ctx->image_decoder = avcodec_alloc_context3(ctx->image_codec);

  if (ctx->image_decoder == NULL) {
    return PBD_ERROR;
  }

  /*
  -------------------------------------------------------------
      Open the decoder.
  -------------------------------------------------------------
  */

  result = avcodec_open2(ctx->image_decoder, ctx->image_codec, NULL);

  if (result < 0) {
    ffmpeg_release(ctx);

    return PBD_ERROR;
  }

  ctx->decoder_initialized = 1;

  return PBD_SUCCESS;
}

/*
=====================================================================
    Video encoder initialization
=====================================================================
*/

/*
 * Creates and configures the video encoder.
 *
 * This function must be called only after decoding the first image,
 * because only then width, height and pixel format are known.
 */
int ffmpeg_open_video_encoder(EncoderContext *ctx) {
  int result;

  if (ctx == NULL) {
    return PBD_ERROR;
  }

  /*
  -------------------------------------------------------------
      Allocate the encoder context.
  -------------------------------------------------------------
  */

  ctx->video_encoder = avcodec_alloc_context3(ctx->video_codec);

  if (ctx->video_encoder == NULL) {
    return PBD_ERROR;
  }

  /*
  -------------------------------------------------------------
      Configure video properties.
  -------------------------------------------------------------
  */

  ctx->video_encoder->codec_id = ctx->video_codec->id;

  ctx->video_encoder->codec_type = AVMEDIA_TYPE_VIDEO;

  ctx->video_encoder->width = ctx->width;

  ctx->video_encoder->height = ctx->height;

  result = ffmpeg_configure_video_encoder(ctx);

  if (result != PBD_SUCCESS) {
    ffmpeg_release(ctx);

    return PBD_ERROR;
  }

  /*
      One time unit corresponds to one millisecond.
  */

  ctx->video_encoder->time_base = ctx->time_base;

  ctx->video_encoder->framerate = av_make_q(1000, 1);

  ctx->video_encoder->thread_count = 8;

  /*
  -------------------------------------------------------------
      Global header.

      Required by some container formats.
  -------------------------------------------------------------
  */

  if (ctx->format_ctx->oformat->flags & AVFMT_GLOBALHEADER) {
    ctx->video_encoder->flags |= AV_CODEC_FLAG_GLOBAL_HEADER;
  }

  /*
  -------------------------------------------------------------
      Open the encoder.
  -------------------------------------------------------------
  */

  result = avcodec_open2(ctx->video_encoder, ctx->video_codec, NULL);

  if (result < 0) {
    ffmpeg_release(ctx);

    return PBD_ERROR;
  }

  /*
  -------------------------------------------------------------
      Copy encoder parameters into the output stream.
  -------------------------------------------------------------
  */

  result = avcodec_parameters_from_context(ctx->video_stream->codecpar,
                                           ctx->video_encoder);

  if (result < 0) {
    ffmpeg_release(ctx);

    return PBD_ERROR;
  }

  ctx->video_stream->time_base = ctx->time_base;

  /*
  -------------------------------------------------------------
      Allocate the encoder frame.

      This frame will receive the pixels produced by the image
      decoder (optionally converted through libswscale).
  -------------------------------------------------------------
  */

  ctx->encoder_frame->format = ctx->video_encoder->pix_fmt;

  ctx->encoder_frame->width = ctx->video_encoder->width;

  ctx->encoder_frame->height = ctx->video_encoder->height;

  result = av_frame_get_buffer(ctx->encoder_frame, 32);

  if (result < 0) {
    ffmpeg_release(ctx);

    return PBD_ERROR;
  }

  /*
  -------------------------------------------------------------
      Write the container header.

      At this point the output file is ready to receive frames.
  -------------------------------------------------------------
  */

  result = avformat_write_header(ctx->format_ctx, NULL);

  if (result < 0) {
    ffmpeg_release(ctx);

    return PBD_ERROR;
  }

  // ffmpeg_dump_encoder_configuration(ctx);

  return PBD_SUCCESS;
}

/*
 * Creates the GIF filtering pipeline.
 *
 * Decoded frames enter through buffersrc and are split into two
 * branches. One branch generates the global palette; the other is
 * synchronized with that palette by paletteuse. The final PAL8 frames
 * are exposed through buffersink.
 */
static int ffmpeg_open_gif_filter_graph(EncoderContext *ctx) {
  static const char *filter_description = "[in]split[frames][palette_input];"
                                          "[palette_input]palettegen[palette];"
                                          "[frames][palette]paletteuse[out]";

  const AVFilter *buffer_filter;
  const AVFilter *buffersink_filter;

  AVFilterInOut *inputs;
  AVFilterInOut *outputs;

  char buffer_arguments[256];

  int result;

  if (ctx == NULL || ctx->width <= 0 || ctx->height <= 0 ||
      ctx->pixel_format == AV_PIX_FMT_NONE) {
    return PBD_ERROR;
  }

  if (ctx->filter_graph != NULL) {
    return PBD_SUCCESS;
  }

  buffer_filter = avfilter_get_by_name("buffer");
  buffersink_filter = avfilter_get_by_name("buffersink");

  if (buffer_filter == NULL || buffersink_filter == NULL) {
    return PBD_ERROR;
  }

  ctx->filter_graph = avfilter_graph_alloc();

  if (ctx->filter_graph == NULL) {
    return PBD_ERROR;
  }

  snprintf(buffer_arguments, sizeof(buffer_arguments),
           "video_size=%dx%d:"
           "pix_fmt=%d:"
           "time_base=%d/%d:"
           "pixel_aspect=%d/%d:"
           "colorspace=%d:"
           "range=%d",
           ctx->width, ctx->height, ctx->pixel_format, ctx->time_base.num,
           ctx->time_base.den, ctx->sample_aspect_ratio.num,
           ctx->sample_aspect_ratio.den, ctx->color_space, ctx->color_range);

  result = avfilter_graph_create_filter(&ctx->buffersrc_ctx, buffer_filter,
                                        "gif_input", buffer_arguments, NULL,
                                        ctx->filter_graph);

  if (result < 0) {
    return PBD_ERROR;
  }

  result =
      avfilter_graph_create_filter(&ctx->buffersink_ctx, buffersink_filter,
                                   "gif_output", NULL, NULL, ctx->filter_graph);

  if (result < 0) {
    return PBD_ERROR;
  }

  inputs = avfilter_inout_alloc();
  outputs = avfilter_inout_alloc();

  if (inputs == NULL || outputs == NULL) {
    avfilter_inout_free(&inputs);
    avfilter_inout_free(&outputs);

    return PBD_ERROR;
  }

  outputs->name = av_strdup("in");
  outputs->filter_ctx = ctx->buffersrc_ctx;
  outputs->pad_idx = 0;
  outputs->next = NULL;

  inputs->name = av_strdup("out");
  inputs->filter_ctx = ctx->buffersink_ctx;
  inputs->pad_idx = 0;
  inputs->next = NULL;

  if (outputs->name == NULL || inputs->name == NULL) {
    avfilter_inout_free(&inputs);
    avfilter_inout_free(&outputs);

    return PBD_ERROR;
  }

  result = avfilter_graph_parse_ptr(ctx->filter_graph, filter_description,
                                    &inputs, &outputs, NULL);

  avfilter_inout_free(&inputs);
  avfilter_inout_free(&outputs);

  if (result < 0) {
    return PBD_ERROR;
  }

  result = avfilter_graph_config(ctx->filter_graph, NULL);

  if (result < 0) {
    return PBD_ERROR;
  }

  return PBD_SUCCESS;
}

/*
 * Creates the pixel-format conversion context required by the current
 * encoder.
 *
 * The context is initialized only once because every frame in one
 * encoding session is expected to preserve its dimensions and source
 * pixel format.
 */
static int ffmpeg_create_sws_context(EncoderContext *ctx) {
  enum AVPixelFormat source_pixel_format;
  int source_full_range;
  int result;

  if (ctx == NULL || ctx->video_encoder == NULL) {
    return PBD_ERROR;
  }

  if (ctx->sws != NULL) {
    return PBD_SUCCESS;
  }

  source_pixel_format = ctx->pixel_format;
  source_full_range = 0;

  switch (source_pixel_format) {
  case AV_PIX_FMT_YUVJ420P:
    source_pixel_format = AV_PIX_FMT_YUV420P;
    source_full_range = 1;
    break;

  case AV_PIX_FMT_YUVJ422P:
    source_pixel_format = AV_PIX_FMT_YUV422P;
    source_full_range = 1;
    break;

  case AV_PIX_FMT_YUVJ444P:
    source_pixel_format = AV_PIX_FMT_YUV444P;
    source_full_range = 1;
    break;

  default:
    break;
  }

  ctx->sws = sws_getContext(
      ctx->width, ctx->height, source_pixel_format, ctx->width, ctx->height,
      ctx->video_encoder->pix_fmt, SWS_BILINEAR, NULL, NULL, NULL);

  if (ctx->sws == NULL) {
    return PBD_ERROR;
  }

  if (!source_full_range) {
    return PBD_SUCCESS;
  }

  const int *coefficients = sws_getCoefficients(SWS_CS_DEFAULT);

  result = sws_setColorspaceDetails(ctx->sws, coefficients, 1, coefficients, 0,
                                    0, 1 << 16, 1 << 16);

  if (result < 0) {
    sws_freeContext(ctx->sws);
    ctx->sws = NULL;

    return PBD_ERROR;
  }

  return PBD_SUCCESS;
}

/*
 * Converts the decoded image into the pixel format required by the
 * selected video encoder.
 */
static int ffmpeg_prepare_video_frame(EncoderContext *ctx) {
  int result;

  if (ctx == NULL || ctx->decoded_frame == NULL || ctx->encoder_frame == NULL ||
      ctx->video_encoder == NULL) {
    return PBD_ERROR;
  }

  result = ffmpeg_create_sws_context(ctx);

  if (result != PBD_SUCCESS) {
    return result;
  }

  result = av_frame_make_writable(ctx->encoder_frame);

  if (result < 0) {
    return PBD_ERROR;
  }

  result = sws_scale(ctx->sws, (const uint8_t *const *)ctx->decoded_frame->data,
                     ctx->decoded_frame->linesize, 0, ctx->height,
                     ctx->encoder_frame->data, ctx->encoder_frame->linesize);

  if (result <= 0) {
    return PBD_ERROR;
  }

  return PBD_SUCCESS;
}

/*
 * Prepares a decoded image for video encoding.
 *
 * GIF frames bypass this path because their pixel-format conversion
 * is performed by the dedicated libavfilter graph.
 */
static int ffmpeg_prepare_encoder_frame(EncoderContext *ctx) {
  if (ctx == NULL) {
    return PBD_ERROR;
  }

  return ffmpeg_prepare_video_frame(ctx);
}

/*
 * Replaces deprecated full-range YUVJ pixel formats with their
 * standard YUV equivalents while preserving JPEG full range.
 */
static void ffmpeg_normalize_decoded_frame(AVFrame *frame) {
  if (frame == NULL) {
    return;
  }

  switch (frame->format) {
  case AV_PIX_FMT_YUVJ420P:
    frame->format = AV_PIX_FMT_YUV420P;
    frame->color_range = AVCOL_RANGE_JPEG;
    break;

  case AV_PIX_FMT_YUVJ411P:
    frame->format = AV_PIX_FMT_YUV411P;
    frame->color_range = AVCOL_RANGE_JPEG;
    break;

  case AV_PIX_FMT_YUVJ422P:
    frame->format = AV_PIX_FMT_YUV422P;
    frame->color_range = AVCOL_RANGE_JPEG;
    break;

  case AV_PIX_FMT_YUVJ444P:
    frame->format = AV_PIX_FMT_YUV444P;
    frame->color_range = AVCOL_RANGE_JPEG;
    break;

  case AV_PIX_FMT_YUVJ440P:
    frame->format = AV_PIX_FMT_YUV440P;
    frame->color_range = AVCOL_RANGE_JPEG;
    break;

  default:
    break;
  }
}

/*
=====================================================================
    Image decoding
=====================================================================
*/

/*
 * Decodes one compressed image into a reusable AVFrame.
 *
 * On the first invocation this function also initializes the image
 * decoder and extracts the video properties required to initialize
 * the video encoder.
 */
int ffmpeg_decode_image(EncoderContext *ctx, const void *data, size_t size) {
  int result;

  if (ctx == NULL || data == NULL || size == 0) {
    return PBD_ERROR;
  }

  /*
  -------------------------------------------------------------
      Initialize the decoder only once.
  -------------------------------------------------------------
  */

  if (!ctx->decoder_initialized) {
    result = ffmpeg_open_image_decoder(ctx, data, size);

    if (result != PBD_SUCCESS) {
      return result;
    }
  }

  /*
  -------------------------------------------------------------
      Prepare the reusable packet.
  -------------------------------------------------------------
  */

  av_packet_unref(ctx->decode_packet);

  result = av_new_packet(ctx->decode_packet, (int)size);

  if (result < 0) {
    return PBD_ERROR;
  }

  memcpy(ctx->decode_packet->data, data, size);

  /*
  -------------------------------------------------------------
      Send the compressed image to the decoder.
  -------------------------------------------------------------
  */

  result = avcodec_send_packet(ctx->image_decoder, ctx->decode_packet);

  if (result < 0) {
    av_packet_unref(ctx->decode_packet);

    return PBD_ERROR;
  }

  /*
  -------------------------------------------------------------
      Receive the decoded image.
  -------------------------------------------------------------
  */

  av_frame_unref(ctx->decoded_frame);

  result = avcodec_receive_frame(ctx->image_decoder, ctx->decoded_frame);

  av_packet_unref(ctx->decode_packet);

  if (result < 0) {
    return PBD_ERROR;
  }

  ffmpeg_normalize_decoded_frame(ctx->decoded_frame);

  /*
  -------------------------------------------------------------
      First decoded image.

      Use it to initialize the video encoder.
  -------------------------------------------------------------
  */

  if (ctx->frame_count == 0) {
    ctx->width = ctx->decoded_frame->width;

    ctx->height = ctx->decoded_frame->height;

    ctx->pixel_format = ctx->decoded_frame->format;

    ctx->sample_aspect_ratio = ctx->decoded_frame->sample_aspect_ratio;

    ctx->color_space = ctx->decoded_frame->colorspace;

    ctx->color_range = ctx->decoded_frame->color_range;

    result = ffmpeg_open_video_encoder(ctx);

    if (result != PBD_SUCCESS) {
      return result;
    }
  }

  return PBD_SUCCESS;
}

/*
=====================================================================
    Video encoding
=====================================================================
*/

/*
 * Sends one fully prepared frame to the video encoder and writes every
 * packet produced by it.
 *
 * The caller is responsible for assigning the frame timestamp and
 * updating the encoding timeline.
 */
int ffmpeg_encode_frame(EncoderContext *ctx) {
  int result;

  if (ctx == NULL || ctx->video_encoder == NULL || ctx->encoder_frame == NULL ||
      ctx->encode_packet == NULL || ctx->video_stream == NULL ||
      ctx->format_ctx == NULL) {
    return PBD_ERROR;
  }

  result = avcodec_send_frame(ctx->video_encoder, ctx->encoder_frame);

  if (result < 0) {
    return PBD_ERROR;
  }

  while (1) {
    av_packet_unref(ctx->encode_packet);

    result = avcodec_receive_packet(ctx->video_encoder, ctx->encode_packet);

    if (result == AVERROR(EAGAIN)) {
      break;
    }

    if (result == AVERROR_EOF) {
      break;
    }

    if (result < 0) {
      return PBD_ERROR;
    }

    ctx->encode_packet->stream_index = ctx->video_stream->index;

    av_packet_rescale_ts(ctx->encode_packet, ctx->video_encoder->time_base,
                         ctx->video_stream->time_base);

    result = av_interleaved_write_frame(ctx->format_ctx, ctx->encode_packet);

    av_packet_unref(ctx->encode_packet);

    if (result < 0) {
      return PBD_ERROR;
    }
  }

  return PBD_SUCCESS;
}

/*
=====================================================================
    Encoder shutdown
=====================================================================
*/

/*
 * Flushes the GIF filter graph.
 *
 * After EOF is sent to the buffersrc, palettegen computes the global
 * palette and paletteuse starts emitting PAL8 frames through the
 * buffersink.
 */
static int ffmpeg_flush_gif_filter_graph(EncoderContext *ctx) {
  int result;

  if (ctx == NULL) {
    return PBD_ERROR;
  }

  result = av_buffersrc_add_frame_flags(ctx->buffersrc_ctx, NULL,
                                        AV_BUFFERSRC_FLAG_KEEP_REF);

  if (result < 0) {
    return PBD_ERROR;
  }

  while (1) {
    av_frame_unref(ctx->encoder_frame);

    result = av_buffersink_get_frame(ctx->buffersink_ctx, ctx->encoder_frame);

    if (result == AVERROR(EAGAIN)) {
      break;
    }

    if (result == AVERROR_EOF) {
      break;
    }

    if (result < 0) {
      return PBD_ERROR;
    }

    result = ffmpeg_encode_frame(ctx);

    if (result != PBD_SUCCESS) {
      return result;
    }
  }

  return PBD_SUCCESS;
}

/*
 * Flushes every delayed frame from the encoder.
 */
int ffmpeg_flush_encoder(EncoderContext *ctx) {
  int result;

  if (ctx == NULL) {
    return PBD_ERROR;
  }

  /*
  -------------------------------------------------------------
      Signal end of input.

      Passing NULL tells FFmpeg that no more frames will arrive.
  -------------------------------------------------------------
  */

  result = avcodec_send_frame(ctx->video_encoder, NULL);

  if (result < 0) {
    return PBD_ERROR;
  }

  /*
  -------------------------------------------------------------
      Retrieve every delayed packet.
  -------------------------------------------------------------
  */

  while (1) {
    av_packet_unref(ctx->encode_packet);

    result = avcodec_receive_packet(ctx->video_encoder, ctx->encode_packet);

    if (result == AVERROR(EAGAIN)) {
      break;
    }

    if (result == AVERROR_EOF) {
      break;
    }

    if (result < 0) {
      return PBD_ERROR;
    }

    ctx->encode_packet->stream_index = ctx->video_stream->index;

    av_packet_rescale_ts(ctx->encode_packet, ctx->video_encoder->time_base,
                         ctx->video_stream->time_base);

    result = av_interleaved_write_frame(ctx->format_ctx, ctx->encode_packet);

    av_packet_unref(ctx->encode_packet);

    if (result < 0) {
      return PBD_ERROR;
    }
  }

  return PBD_SUCCESS;
}

/*
=====================================================================
    Session termination
=====================================================================
*/

/*
 * Flushes the encoder, writes the trailer and releases every
 * allocated FFmpeg object.
 */
int ffmpeg_encoder_close(EncoderContext *ctx) {
  int result;

  if (ctx == NULL) {
    return PBD_ERROR;
  }

  /*
  -------------------------------------------------------------
      Flush pending GIF frames.

      GIF encoding requires draining the filter graph before the
      video encoder itself can be flushed.
  -------------------------------------------------------------
  */

  if (strcmp(ctx->codec_name, "gif") == 0) {
    result = ffmpeg_flush_gif_filter_graph(ctx);

    if (result != PBD_SUCCESS) {
      ffmpeg_release(ctx);

      return result;
    }
  }

  /*
  -------------------------------------------------------------
      Flush delayed encoder frames.
  -------------------------------------------------------------
  */

  result = ffmpeg_flush_encoder(ctx);

  if (result != PBD_SUCCESS) {
    ffmpeg_release(ctx);

    return result;
  }

  /*
  -------------------------------------------------------------
      Finalize the output container.
  -------------------------------------------------------------
  */

  if (ctx->format_ctx != NULL) {
    result = av_write_trailer(ctx->format_ctx);

    if (result < 0) {
      ffmpeg_release(ctx);

      return PBD_ERROR;
    }
  }

  /*
  -------------------------------------------------------------
      Release every allocated resource.
  -------------------------------------------------------------
  */

  ffmpeg_release(ctx);

  return PBD_SUCCESS;
}

/*
=====================================================================
    Resource cleanup
=====================================================================
*/

/*
 * Releases every FFmpeg object owned by the encoder context.
 *
 * This function is intentionally idempotent and can safely be called
 * multiple times.
 */
void ffmpeg_release(EncoderContext *ctx) {
  if (ctx == NULL) {
    return;
  }

  /*
  -------------------------------------------------------------
      GIF filter graph
  -------------------------------------------------------------
  */

  if (ctx->filter_graph != NULL) {
    avfilter_graph_free(&ctx->filter_graph);
  }

  ctx->buffersrc_ctx = NULL;
  ctx->buffersink_ctx = NULL;

  /*
  -------------------------------------------------------------
      Pixel format converter
  -------------------------------------------------------------
  */

  if (ctx->sws != NULL) {
    sws_freeContext(ctx->sws);

    ctx->sws = NULL;
  }

  /*
  -------------------------------------------------------------
      Frames
  -------------------------------------------------------------
  */

  if (ctx->decoded_frame != NULL) {
    av_frame_free(&ctx->decoded_frame);
  }

  if (ctx->encoder_frame != NULL) {
    av_frame_free(&ctx->encoder_frame);
  }

  /*
  -------------------------------------------------------------
      Packets
  -------------------------------------------------------------
  */

  if (ctx->decode_packet != NULL) {
    av_packet_free(&ctx->decode_packet);
  }

  if (ctx->encode_packet != NULL) {
    av_packet_free(&ctx->encode_packet);
  }

  /*
  -------------------------------------------------------------
      Codec contexts
  -------------------------------------------------------------
  */

  if (ctx->image_decoder != NULL) {
    avcodec_free_context(&ctx->image_decoder);
  }

  if (ctx->video_encoder != NULL) {
    avcodec_free_context(&ctx->video_encoder);
  }

  /*
  -------------------------------------------------------------
      Output file
  -------------------------------------------------------------
  */

  if (ctx->format_ctx != NULL) {
    if (!(ctx->format_ctx->oformat->flags & AVFMT_NOFILE)) {
      if (ctx->format_ctx->pb != NULL) {
        avio_closep(&ctx->format_ctx->pb);
      }
    }

    avformat_free_context(ctx->format_ctx);

    ctx->format_ctx = NULL;
  }

  /*
  -------------------------------------------------------------
      Reset runtime state
  -------------------------------------------------------------
  */

  ctx->video_stream = NULL;

  ctx->video_codec = NULL;
  ctx->image_codec = NULL;

  ctx->image_codec_id = AV_CODEC_ID_NONE;

  ctx->width = 0;
  ctx->height = 0;

  ctx->pixel_format = AV_PIX_FMT_NONE;

  ctx->current_pts = 0;
  ctx->current_time_ms = 0;

  ctx->time_base.num = 0;
  ctx->time_base.den = 0;

  ctx->frame_count = 0;

  ctx->initialized = 0;
  ctx->decoder_initialized = 0;

  ctx->output_file[0] = '\0';
  ctx->format_name[0] = '\0';
  ctx->codec_name[0] = '\0';
}
