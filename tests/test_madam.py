import io

import piexif
import pytest

from madam import Madam
from madam.core import Asset, UnsupportedFormatError
from assets import asset
from assets import image_asset, jpeg_asset, png_asset, gif_asset
from assets import audio_asset, mp3_asset, wav_asset
from assets import video_asset, mp4_asset, y4m_asset


@pytest.fixture(name='madam', scope='class')
def madam_instance():
    return Madam()


def test_jpeg_asset_essence_does_not_contain_exif_metadata(madam):
    exif = jpeg_asset().metadata['exif']
    data_with_exif = io.BytesIO()
    piexif.insert(piexif.dump(exif), jpeg_asset().essence.read(), new_file=data_with_exif)
    asset = madam.read(data_with_exif)
    essence_bytes = asset.essence.read()

    essence_exif = piexif.load(essence_bytes)

    for ifd, ifd_data in essence_exif.items():
        assert not ifd_data


def test_read_empty_file_raises_error(madam):
    file_data = io.BytesIO()

    with pytest.raises(UnsupportedFormatError):
        madam.read(file_data)


def test_read_raises_when_file_is_none(madam):
    invalid_file = None

    with pytest.raises(TypeError):
        madam.read(invalid_file)


def test_read_raises_error_when_format_is_unknown(madam):
    random_data = b'\x07]>e\x10\n+Y\x07\xd8\xf4\x90%\r\xbbK\xb8+\xf3v%\x0f\x11'
    unknown_file = io.BytesIO(random_data)

    with pytest.raises(UnsupportedFormatError):
        madam.read(unknown_file)


@pytest.fixture(scope='class')
def read_asset(madam, asset):
    return madam.read(asset.essence)


def test_read_returns_asset_when_reading_valid_data(read_asset):
    assert read_asset is not None


def test_read_image_returns_asset_with_image_mime_type(madam, asset):
    read_asset = madam.read(asset.essence)
    assert read_asset.mime_type == asset.mime_type


def test_read_returns_asset_whose_essence_is_filled(read_asset):
    assert read_asset.essence.read()


def test_read_jpeg_does_not_alter_the_original_file(madam):
    jpeg_data = jpeg_asset().essence
    original_image_data = jpeg_data.read()
    jpeg_data.seek(0)

    madam.read(jpeg_data)

    jpeg_data.seek(0)
    image_data_after_reading = jpeg_data.read()
    assert original_image_data == image_data_after_reading


def test_read_video_returns_asset_with_duration_metadata(madam, video_asset):
    asset = madam.read(video_asset.essence)

    assert asset.duration == video_asset.duration


def test_read_returns_asset_containing_image_size_metadata(madam, image_asset):
    image_data = image_asset.essence

    asset = madam.read(image_data)

    assert asset.metadata['width'] == 4
    assert asset.metadata['height'] == 3


def test_writes_correct_essence_without_metadata(madam, image_asset):
    asset = Asset(essence=image_asset.essence)
    file = io.BytesIO()

    madam.write(asset, file)

    file.seek(0)
    assert file.read() == asset.essence.read()


def test_writes_correct_essence_with_metadata(madam, jpeg_asset):
    file = io.BytesIO()

    madam.write(jpeg_asset, file)

    file.seek(0)
    assert file.read() != jpeg_asset.essence.read()


def test_config_contains_list_of_all_processors_by_default(madam):
    assert madam.config['processors'] == [
        'madam.audio.MutagenProcessor',
        'madam.image.PillowProcessor',
        'madam.ffmpeg.FFmpegProcessor']
