import datetime
import io
import subprocess
from fractions import Fraction
from xml.etree import ElementTree as ET

import PIL.Image
import pytest

import madam.core
from madam.future import subprocess_run


DEFAULT_WIDTH = 24
DEFAULT_HEIGHT = 12
DEFAULT_DURATION = 0.2


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


@pytest.fixture(scope='class')
def jpeg_asset(width=DEFAULT_WIDTH, height=DEFAULT_HEIGHT, transpositions=None, **additional_metadata):
    if not transpositions:
        transpositions = []
    image = image_rgb(width=width, height=height, transpositions=transpositions)
    essence = io.BytesIO()
    image.save(essence, 'JPEG', quality=100)
    essence.seek(0)
    metadata = dict(
        exif={
            'aperture': 0.02,
            'artist': 'Test Artist',
            'brightness': 2.15,
            'camera.manufacturer': 'Test Manufacturer, Inc.',
            'camera.model': 'TestCamera 40 Mark II',
            'description': 'A plastic bag in the street',
            'exposure_time': 0.4,
            'firmware': 'TestCamera v1.07',
            'fnumber': 2.8,
            'focal_length': 28,
            'focal_length_35mm': 42,
            'gps.altitude': 519,
            'gps.altitude_ref': 'm_above_sea_level',
            'gps.latitude': (48, 8, 6),
            'gps.latitude_ref': 'north',
            'gps.longitude': (11, 34, 55),
            'gps.longitude_ref': 'east',
            'gps.map_datum': 'WGS-84',
            'gps.speed': 0.042,
            'gps.speed_ref': 'km/h',
            'gps.date_stamp': datetime.date(2000, 1, 1),
            'gps.time_stamp': datetime.time(23, 59, 42),
            'lens.manufacturer': 'Yeiss',
            'lens.model': 'Yokton AF 17-50mm F2.8',
            'shutter_speed': 0.01,
            'software': 'MADAM',
        },
        iptc={
            'bylines': ('The', 'Creators'),
            'byline_titles': ('Dr.', 'Prof.'),
            'caption': 'A test image.',
            'contacts': ('Me', 'Myself'),
            'copyright': 'Nobody',
            'creation_date': datetime.date(2000, 1, 1),
            'creation_time': datetime.time(23, 59, 43),
            'credit': 'Devs',
            'expiration_date': datetime.date(2100, 1, 1),
            'expiration_time': datetime.time(23, 59, 44),
            'headline': 'Wonderful Test Image',
            'keywords': ('test', 'image', 'kws'),
            'language': 'English',
            'release_date': datetime.date(2016, 1, 1),
            'release_time': datetime.time(23, 59, 45),
            'source': 'Test suite',
            'subjects': ('The', 'topics'),
        },
        width=width,
        height=height,
        mime_type='image/jpeg'
    )
    metadata.update(additional_metadata)
    return madam.core.Asset(essence, **metadata)


@pytest.fixture(scope='class')
def jpeg_data_with_exif():
    with open('tests/resources/image_with_exif.jpg', 'rb') as file:
        binary_data = file.read()
    return io.BytesIO(binary_data)


@pytest.fixture(scope='class')
def png_asset(width=DEFAULT_WIDTH, height=DEFAULT_HEIGHT):
    image = image_rgb(width=width, height=height)
    essence = io.BytesIO()
    image.save(essence, 'PNG')
    essence.seek(0)
    metadata = dict(
        width=image.width,
        height=image.height,
        mime_type='image/png'
    )
    return madam.core.Asset(essence, **metadata)


@pytest.fixture(scope='class')
def gif_asset(width=DEFAULT_WIDTH, height=DEFAULT_HEIGHT):
    image = image_rgb(width=width, height=height)
    essence = io.BytesIO()
    image.save(essence, 'GIF')
    essence.seek(0)
    metadata = dict(
        width=image.width,
        height=image.height,
        mime_type='image/gif'
    )
    return madam.core.Asset(essence, **metadata)


@pytest.fixture(scope='class')
def svg_asset():
    metadata = dict(rdf=
        dict(xml=
             '<rdf:Description rdf:about="svg_with_metadata.svg">'
             '<dc:format>image/svg+xml</dc:format>'
             '<dc:type>Image</dc:type>'
             '<dc:creator opf:role="aut">John Doe</dc:creator>'
             '<dc:description>Example SVG file with metadata</dc:description>'
             '<dc:rights>Copyright 2016 Erich Seifert</dc:rights>'
             '<dc:date opf:event="creation">2016-11-01</dc:date>'
             '<dc:title>SVG metadata example</dc:title>'
             '<dc:subject>SVG, metadata, RDF, Dublin Core, example</dc:subject>'
             '<dc:source>Various</dc:source>'
             '<dc:date opf:event="publication">2016-11-02</dc:date>'
             '<dc:date opf:event="expiration">2020-11-01</dc:date>'
             '<dc:language>en</dc:language>'
             '<dc:subject>test resources</dc:subject>'
             '</rdf:Description>'
        )
    )

    with open('tests/resources/svg_with_metadata.svg', 'rb') as file:
        tree = ET.parse(file)

    # Remove metadata from essence
    root = tree.getroot()
    metadata_elem = root.find('./{http://www.w3.org/2000/svg}metadata')
    if metadata_elem is not None:
        root.remove(metadata_elem)
    essence = io.BytesIO()
    tree.write(essence)
    essence.seek(0)

    return madam.core.Asset(essence=essence, mime_type='image/svg+xml',
                            width=DEFAULT_WIDTH, height=DEFAULT_HEIGHT,
                            **metadata)


@pytest.fixture(params=['jpeg_asset', 'png_asset', 'gif_asset'])
def image_asset(request, jpeg_asset, png_asset, gif_asset):
    if request.param == 'jpeg_asset':
        return jpeg_asset
    if request.param == 'png_asset':
        return png_asset
    if request.param == 'gif_asset':
        return gif_asset
    raise ValueError()


@pytest.fixture(scope='class')
def wav_asset(tmpdir_factory):
    duration = DEFAULT_DURATION
    command = ('ffmpeg -loglevel error -f lavfi -i sine=frequency=440:duration=%.1f '
               '-vn -c:a pcm_s16le -f wav' % duration).split()
    tmpfile = tmpdir_factory.mktemp('wav_asset').join('without_metadata.wav')
    command.append(str(tmpfile))
    subprocess_run(command, check=True, stderr=subprocess.PIPE)
    with tmpfile.open('rb') as file:
        essence = file.read()
    return madam.core.Asset(essence=io.BytesIO(essence), mime_type='audio/wav',
                            duration=duration)


@pytest.fixture(scope='class')
def mp3_asset(tmpdir_factory):
    duration = DEFAULT_DURATION
    command = ('ffmpeg -loglevel error -f lavfi -i sine=frequency=440:duration=%.1f '
               '-write_xing 0 -id3v2_version 0 -write_id3v1 0 '
               '-vn -f mp3' % duration).split()
    tmpfile = tmpdir_factory.mktemp('mp3_asset').join('without_metadata.mp3')
    command.append(str(tmpfile))
    subprocess_run(command, check=True, stderr=subprocess.PIPE)
    with tmpfile.open('rb') as file:
        essence = file.read()
    return madam.core.Asset(essence=io.BytesIO(essence), mime_type='audio/mpeg',
                            duration=duration)


@pytest.fixture(scope='class')
def opus_asset(tmpdir_factory):
    duration = DEFAULT_DURATION
    command = ('ffmpeg -loglevel error -f lavfi -i sine=frequency=440:duration=%.1f '
               '-vn -f opus' % duration).split()
    tmpfile = tmpdir_factory.mktemp('opus_asset').join('without_metadata.opus')
    command.append(str(tmpfile))
    subprocess_run(command, check=True, stderr=subprocess.PIPE)
    with tmpfile.open('rb') as file:
        essence = file.read()
    return madam.core.Asset(essence=io.BytesIO(essence), mime_type='audio/ogg',
                            duration=duration)


@pytest.fixture(scope='class')
def nut_audio_asset(tmpdir_factory):
    duration = DEFAULT_DURATION
    command = ('ffmpeg -loglevel error -f lavfi -i sine=frequency=440:duration=%.1f '
               '-vn -c:a pcm_s16le -f nut' % duration).split()
    tmpfile = tmpdir_factory.mktemp('nut_asset').join('without_metadata.nut')
    command.append(str(tmpfile))
    subprocess_run(command, check=True, stderr=subprocess.PIPE)
    with tmpfile.open('rb') as file:
        essence = file.read()
    return madam.core.Asset(essence=io.BytesIO(essence), mime_type='audio/x-nut',
                            duration=duration)


@pytest.fixture(scope='class', params=['mp3_asset', 'opus_asset', 'wav_asset'])
def audio_asset(request, mp3_asset, opus_asset, wav_asset):
    if request.param == 'mp3_asset':
        return mp3_asset
    if request.param == 'opus_asset':
        return opus_asset
    if request.param == 'wav_asset':
        return wav_asset
    raise ValueError()


@pytest.fixture(scope='class')
def mp4_asset(tmpdir_factory):
    ffmpeg_params = dict(
        width=DEFAULT_WIDTH,
        height=DEFAULT_HEIGHT,
        duration=DEFAULT_DURATION,
    )
    command = ('ffmpeg -loglevel error '
               '-f lavfi -i color=color=red:size=%(width)dx%(height)d:duration=%(duration).1f:rate=15 '
               '-f lavfi -i sine=frequency=440:duration=%(duration).1f '
               '-strict -2 -c:v h264 -preset ultrafast -qp 0 -c:a aac -f mp4' % ffmpeg_params).split()
    tmpfile = tmpdir_factory.mktemp('mp4_asset').join('lossless.mp4')
    command.append(str(tmpfile))
    subprocess_run(command, check=True, stderr=subprocess.PIPE)
    with tmpfile.open('rb') as file:
        essence = file.read()
    return madam.core.Asset(essence=io.BytesIO(essence), mime_type='video/quicktime',
                            width=DEFAULT_WIDTH, height=DEFAULT_HEIGHT, duration=DEFAULT_DURATION)


@pytest.fixture(scope='class')
def mkv_video_asset(tmpdir_factory):
    ffmpeg_params = dict(
        width=DEFAULT_WIDTH,
        height=DEFAULT_HEIGHT,
        duration=DEFAULT_DURATION,
    )
    command = ('ffmpeg -loglevel error '
               '-f lavfi -i color=color=red:size=%(width)dx%(height)d:duration=%(duration).1f:rate=15 '
               '-f lavfi -i sine=frequency=440:duration=%(duration).1f '
               '-c:v vp9 -c:a libopus -f matroska' % ffmpeg_params).split()
    tmpfile = tmpdir_factory.mktemp('mkv_video_asset').join('vp9-opus.mkv')
    command.append(str(tmpfile))
    subprocess_run(command, check=True, stderr=subprocess.PIPE)
    with tmpfile.open('rb') as file:
        essence = file.read()
    return madam.core.Asset(essence=io.BytesIO(essence), mime_type='video/x-matroska',
                            width=DEFAULT_WIDTH, height=DEFAULT_HEIGHT, duration=DEFAULT_DURATION)


@pytest.fixture(scope='class')
def ogg_video_asset(tmpdir_factory):
    ffmpeg_params = dict(
        width=DEFAULT_WIDTH,
        height=DEFAULT_HEIGHT,
        duration=DEFAULT_DURATION,
    )
    command = ('ffmpeg -loglevel error '
               '-f lavfi -i color=color=red:size=%(width)dx%(height)d:duration=%(duration).1f:rate=15 '
               '-f lavfi -i sine=frequency=440:duration=%(duration).1f '
               '-strict -2 -c:v theora -c:a vorbis -ac 2 -f ogg' % ffmpeg_params).split()
    tmpfile = tmpdir_factory.mktemp('ogg_video_asset').join('theora-vorbis.ogg')
    command.append(str(tmpfile))
    subprocess_run(command, check=True, stderr=subprocess.PIPE)
    with tmpfile.open('rb') as file:
        essence = file.read()
    return madam.core.Asset(essence=io.BytesIO(essence), mime_type='video/ogg',
                            width=DEFAULT_WIDTH, height=DEFAULT_HEIGHT, duration=DEFAULT_DURATION)


@pytest.fixture(scope='class')
def nut_video_asset():
    ffmpeg_params = dict(
        width=DEFAULT_WIDTH,
        height=DEFAULT_HEIGHT,
        duration=DEFAULT_DURATION,
    )
    command = ('ffmpeg -loglevel error '
               '-f lavfi -i color=color=red:size=%(width)dx%(height)d:duration=%(duration).1f:rate=15 '
               '-f lavfi -i sine=frequency=440:duration=%(duration).1f '
               '-c:v ffv1 -level 3 -a:c pcm_s16le -f nut pipe:' % ffmpeg_params).split()
    ffmpeg = subprocess_run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return madam.core.Asset(essence=io.BytesIO(ffmpeg.stdout), mime_type='video/x-nut',
                            width=DEFAULT_WIDTH, height=DEFAULT_HEIGHT, duration=DEFAULT_DURATION)


@pytest.fixture(scope='class', params=['mp4_asset', 'mkv_video_asset'])
def video_asset(request, mp4_asset, mkv_video_asset):
    if request.param == 'mp4_asset':
        return mp4_asset
    elif request.param == 'mkv_video_asset':
        return mkv_video_asset
    else:
        raise ValueError()


@pytest.fixture(scope='class', params=[
    'jpeg_asset', 'png_asset', 'gif_asset', 'svg_asset',
    'mp3_asset', 'opus_asset', 'wav_asset',
    'mp4_asset', 'mkv_video_asset', 'ogg_video_asset'])
def asset(request,
          jpeg_asset, png_asset, gif_asset, svg_asset,
          mp3_asset, opus_asset, wav_asset,
          mp4_asset, mkv_video_asset, ogg_video_asset):
    if request.param == 'jpeg_asset':
        return jpeg_asset
    if request.param == 'png_asset':
        return png_asset
    if request.param == 'gif_asset':
        return gif_asset
    if request.param == 'svg_asset':
        return svg_asset
    if request.param == 'mp3_asset':
        return mp3_asset
    if request.param == 'opus_asset':
        return opus_asset
    if request.param == 'wav_asset':
        return wav_asset
    if request.param == 'mp4_asset':
        return mp4_asset
    if request.param == 'mkv_video_asset':
        return mkv_video_asset
    if request.param == 'ogg_video_asset':
        return ogg_video_asset
    raise ValueError()


@pytest.fixture
def unknown_asset():
    random_data = b'\x07]>e\x10\n+Y\x07\xd8\xf4\x90%\r\xbbK\xb8+\xf3v%\x0f\x11'
    return madam.core.Asset(essence=io.BytesIO(random_data),
                            mime_type='application/octet-stream')
