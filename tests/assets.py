import io
import subprocess

import piexif
import PIL.Image
import pytest

import madam.core
from madam.future import subprocess_run


def image_rgb(width, height, transpositions=None):
    if not transpositions:
        transpositions = []
    image = PIL.Image.new('RGB', (width, height))
    # Fill the image with a shape which is (probably) not invariant towards
    # rotations or flips as long as the image has a size of (2, 2) or greater
    for y in range(0, height):
        for x in range(0, width):
            color = (255, 255, 255) if y == 0 or x == 0 else (0, 0, 0)
            image.putpixel((x, y), color)
    for transposition in transpositions:
        image = image.transpose(transposition)
    return image


def jpeg_rgb(width=4, height=3, transpositions=None):
    if not transpositions:
        transpositions = []
    image = image_rgb(width=width, height=height, transpositions=transpositions)
    image_data = io.BytesIO()
    image.save(image_data, 'JPEG', quality=100)
    image_data.seek(0)
    return image_data


def png_rgb(width, height):
    image = image_rgb(width, height)
    image_data = io.BytesIO()
    image.save(image_data, 'PNG')
    image_data.seek(0)
    return image_data


def add_exif_to_jpeg(exif, image_data):
    exif_bytes = piexif.dump(exif)
    image_with_exif_metadata = io.BytesIO()
    piexif.insert(exif_bytes, image_data.read(), image_with_exif_metadata)
    return image_with_exif_metadata


@pytest.fixture
def jpeg_asset(width=4, height=3, transpositions=None, **additional_metadata):
    if not transpositions:
        transpositions = []
    essence = jpeg_rgb(width=width, height=height, transpositions=transpositions)
    metadata = dict(
        exif={'0th': {piexif.ImageIFD.Artist: b'Test artist'}},
        width=width,
        height=height,
        mime_type='image/jpeg'
    )
    metadata.update(additional_metadata)
    asset = madam.core.Asset(essence, **metadata)
    return asset


@pytest.fixture
def png_asset():
    width = 4
    height = 3
    essence = png_rgb(width, height)
    metadata = dict(
        width=width,
        height=height,
        mime_type='image/png'
    )
    asset = madam.core.Asset(essence, **metadata)
    return asset


@pytest.fixture(params=['jpeg_asset', 'png_asset'])
def image_asset(request, jpeg_asset, png_asset):
    if request.param == 'jpeg_asset':
        return jpeg_asset
    else:
        return png_asset


@pytest.fixture
def wav_asset():
    with open('tests/resources/16-bit-mono.wav', 'rb') as file:
        essence = file.read()
    return madam.core.Asset(essence=io.BytesIO(essence),
                            mime_type='audio/wav',
                            duration=0.1)


@pytest.fixture
def mp3_asset():
    with open('tests/resources/64kbits.mp3', 'rb') as file:
        essence = file.read()
    return madam.core.Asset(essence=io.BytesIO(essence),
                            mime_type='audio/mpeg',
                            duration=0.144)


@pytest.fixture
def y4m_asset():
    command = 'ffmpeg -loglevel error -f lavfi -i color=color=red:duration=0.2:rate=15 ' \
              '-f yuv4mpegpipe pipe:'.split()
    ffmpeg = subprocess_run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return madam.core.Asset(essence=io.BytesIO(ffmpeg.stdout),
                            mime_type='video/x-yuv4mpegpipe',
                            duration=0.2)


@pytest.fixture(params=['jpeg_asset', 'png_asset', 'mp3_asset', 'wav_asset', 'y4m_asset'])
def asset(request, jpeg_asset, png_asset, mp3_asset, wav_asset, y4m_asset):
    if request.param == 'jpeg_asset':
        return jpeg_asset
    elif request.param == 'png_asset':
        return png_asset
    elif request.param == 'mp3_asset':
        return mp3_asset
    elif request.param == 'wav_asset':
        return wav_asset
    else:
        return y4m_asset


@pytest.fixture
def unknown_asset():
    random_data = b'\x07]>e\x10\n+Y\x07\xd8\xf4\x90%\r\xbbK\xb8+\xf3v%\x0f\x11'
    return madam.core.Asset(essence=io.BytesIO(random_data),
                            mime_type='application/octet-stream')
