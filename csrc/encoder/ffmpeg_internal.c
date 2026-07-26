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

#include <libavutil/opt.h>
#include <libavutil/pixdesc.h>

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

static int ffmpeg_prepare_video_frame(EncoderContext *ctx);
static int ffmpeg_prepare_encoder_frame(EncoderContext *ctx);

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

  strncpy(destination, source, destination_size - 1);

  destination[destination_size - 1] = '\0';
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

    result = av_opt_set_int(ctx->video_encoder->priv_data, "crf", 32, 0);

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
                        const char *format, const char *codec,
                        const uint32_t *palette, size_t palette_size) {

  if (ctx == NULL) {
    return PBD_ERROR;
  }

  memset(ctx, 0, sizeof(*ctx));

  copy_string(ctx->output_file, sizeof(ctx->output_file), output_file);

  copy_string(ctx->format_name, sizeof(ctx->format_name), format);

  copy_string(ctx->codec_name, sizeof(ctx->codec_name), codec);

  if (palette != NULL && palette_size > 0) {
    if (palette_size > 256) {
      palette_size = 256;
    }

    memcpy(ctx->gif_palette, palette, palette_size * sizeof(uint32_t));

    ctx->gif_palette_size = palette_size;
  }

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
 * ???????????????????????????????????????????
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

  result = ffmpeg_prepare_encoder_frame(ctx);

  if (result != PBD_SUCCESS) {
    return result;
  }

  return ffmpeg_encode_frame(ctx, duration_ms);
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
  const AVCodecDescriptor *descriptor;
  const AVCodecParameters *parameters = NULL;
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
      Retrieve the codec descriptor associated with the detected
      demuxer.
  -------------------------------------------------------------
  */
  /*
  #if LIBAVFORMAT_VERSION_MAJOR >= 59

    parameters = input_format->codec_tag;

  #else

    parameters = NULL;

  #endif
  */
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

  return PBD_SUCCESS;
}

/*
 * Converts the decoded image into the pixel format required by the
 * selected video encoder.
 */
static int ffmpeg_prepare_video_frame(EncoderContext *ctx) {
  enum AVPixelFormat source_pixel_format;
  int source_full_range;
  int result;

  if (ctx == NULL || ctx->decoded_frame == NULL || ctx->encoder_frame == NULL ||
      ctx->video_encoder == NULL) {
    return PBD_ERROR;
  }

  /*
   * Create the conversion context only once, after the first image
   * has provided the source dimensions and pixel format.
   */
  if (ctx->sws == NULL) {
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

    if (source_full_range) {
      const int *coefficients;

      coefficients = sws_getCoefficients(SWS_CS_DEFAULT);

      result = sws_setColorspaceDetails(ctx->sws, coefficients, 1, coefficients,
                                        0, 0, 1 << 16, 1 << 16);

      if (result < 0) {
        return PBD_ERROR;
      }
    }
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
 * Selects the frame preparation path required by the current output
 * encoder.
 */
static int ffmpeg_prepare_encoder_frame(EncoderContext *ctx) {
  return ffmpeg_prepare_video_frame(ctx);
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
 * Encodes one frame and writes the produced packets into the output
 * container.
 */
int ffmpeg_encode_frame(EncoderContext *ctx, uint32_t duration_ms) {
  int result;

  if (ctx == NULL) {
    return PBD_ERROR;
  }

  /*
  -------------------------------------------------------------
      Assign presentation timestamp.

      The time base is expressed in milliseconds.
  -------------------------------------------------------------
  */

  ctx->encoder_frame->pts = ctx->current_pts;

  /*
  -------------------------------------------------------------
      Send the frame to the encoder.
  -------------------------------------------------------------
  */

  result = avcodec_send_frame(ctx->video_encoder, ctx->encoder_frame);

  if (result < 0) {
    return PBD_ERROR;
  }

  /*
  -------------------------------------------------------------
      Read every packet produced by the encoder.

      Some codecs may generate more than one packet for a single
      input frame.
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

    /*
    ---------------------------------------------------------
        Associate the packet with the output stream.
    ---------------------------------------------------------
    */

    ctx->encode_packet->stream_index = ctx->video_stream->index;

    /*
    ---------------------------------------------------------
        Convert timestamps from encoder time base to stream
        time base.
    ---------------------------------------------------------
    */

    av_packet_rescale_ts(ctx->encode_packet, ctx->video_encoder->time_base,
                         ctx->video_stream->time_base);

    /*
    ---------------------------------------------------------
        Write the encoded packet.
    ---------------------------------------------------------
    */

    result = av_interleaved_write_frame(ctx->format_ctx, ctx->encode_packet);

    av_packet_unref(ctx->encode_packet);

    if (result < 0) {
      return PBD_ERROR;
    }
  }

  /*
  -------------------------------------------------------------
      Advance the encoder timeline.
  -------------------------------------------------------------
  */

  ctx->current_pts += duration_ms;

  ctx->current_time_ms += duration_ms;

  ++ctx->frame_count;

  return PBD_SUCCESS;
}

/*
=====================================================================
    Encoder shutdown
=====================================================================
*/

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
      Flush delayed frames.
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
