cmake_minimum_required(VERSION 3.16)

project(
    pbd_encoder
    VERSION 0.1.0
    LANGUAGES C
)

#
# Language configuration
#

set(CMAKE_C_STANDARD 11)
set(CMAKE_C_STANDARD_REQUIRED ON)
set(CMAKE_C_EXTENSIONS OFF)

#
# Compiler warnings
#

if (MSVC)

    add_compile_options(
        /W4
    )

else()

    add_compile_options(
        -Wall
        -Wextra
        -Wpedantic
    )

endif()

#
# FFmpeg
#

set(
    FFMPEG_ROOT
    "C:/Users/pc/pbd/tools/ffmpeg"
)

set(
    FFMPEG_INCLUDE_DIR
    "${FFMPEG_ROOT}/include"
)

set(
    FFMPEG_LIBRARY_DIR
    "${FFMPEG_ROOT}/lib"
)

#
# Encoder library
#

add_library(
    pbd_encoder

    encoder.c
    ffmpeg_internal.c
)

target_include_directories(
    pbd_encoder

    PUBLIC
        ${CMAKE_CURRENT_SOURCE_DIR}
)

target_include_directories(
    pbd_encoder

    SYSTEM PRIVATE
        ${FFMPEG_INCLUDE_DIR}
)

target_link_directories(
    pbd_encoder

    PUBLIC

        ${FFMPEG_LIBRARY_DIR}
)

target_link_libraries(
    pbd_encoder

    PUBLIC

        avcodec
        avformat
        avutil
        avfilter
        swscale
)

#
# Test executable
#

add_executable(

    pbd_encoder_test

    test/main.c
)

if (MSVC)

    target_compile_definitions(
        pbd_encoder_test

        PRIVATE
            _CRT_SECURE_NO_WARNINGS
    )

endif()

target_link_libraries(

    pbd_encoder_test

    PRIVATE

        pbd_encoder
)

#
# Output directories
#

set_target_properties(

    pbd_encoder
    pbd_encoder_test

    PROPERTIES

        ARCHIVE_OUTPUT_DIRECTORY
            ${CMAKE_BINARY_DIR}/lib

        LIBRARY_OUTPUT_DIRECTORY
            ${CMAKE_BINARY_DIR}/lib

        RUNTIME_OUTPUT_DIRECTORY
            ${CMAKE_BINARY_DIR}/bin
)