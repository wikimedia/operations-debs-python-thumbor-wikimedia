import platform
import os.path

from PIL import Image

from ssim import compute_ssim

from tornado.ioloop import IOLoop
from tornado.testing import AsyncHTTPTestCase

from thumbor.config import Config
from thumbor.context import Context, ServerParameters
from thumbor.importer import Importer
from thumbor.utils import which

from wikimedia_thumbor.app import App


class WikimediaTestCase(AsyncHTTPTestCase):
    def get_new_ioloop(self):
        return IOLoop.instance()

    def retrieve(self, url):
        self.http_client.fetch(self.get_url(url), self.stop)
        return self.wait(timeout=300)

    def get_config(self):
        cfg = Config(SECURITY_KEY='ACME-SEC')

        cfg.STORAGE = 'thumbor.storages.no_storage'
        cfg.LOADER = 'thumbor.loaders.file_loader'

        cfg.FILE_LOADER_ROOT_PATH = os.path.join(
            os.path.dirname(__file__),
            'originals'
        )
        cfg.ENGINE = 'wikimedia_thumbor.engine.proxy'
        cfg.RESPECT_ORIENTATION = True

        cfg.FFMPEG_PATH = which('ffmpeg')
        cfg.EXIFTOOL_PATH = which('exiftool')
        cfg.VIPS_PATH = which('vips')
        cfg.FFPROBE_PATH = which('ffprobe')
        cfg.XCF2PNG_PATH = which('xcf2png')
        cfg.GHOSTSCRIPT_PATH = which('gs')
        cfg.DDJVU_PATH = which('ddjvu')
        cfg.RSVG_CONVERT_PATH = which('rsvg-convert')
        timeout = which(
            'gtimeout' if platform.system() == 'Darwin' else 'timeout'
        )
        cfg.SUBPROCESS_TIMEOUT_PATH = timeout

        cfg.SUBPROCESS_USE_TIMEOUT = True
        cfg.SUBPROCESS_TIMEOUT = 60

        cfg.CHROMA_SUBSAMPLING = '4:2:0'
        cfg.QUALITY = 79
        cfg.QUALITY_LOW = 40
        cfg.DEFAULT_FILTERS_JPEG = 'conditional_sharpen(0.0,0.8,1.0,0.0,0.85)'

        cfg.COMMUNITY_EXTENSIONS = [
            'wikimedia_thumbor.handler.multi',
            'wikimedia_thumbor.handler.images',
            'wikimedia_thumbor.handler.core'
        ]

        cfg.EXIF_FIELDS_TO_KEEP = ['Artist', 'Copyright', 'Description']
        cfg.EXIF_TINYRGB_PATH = os.path.join(
            os.path.dirname(__file__),
            'tinyrgb.icc'
        )
        cfg.EXIF_TINYRGB_ICC_REPLACE = 'sRGB IEC61966-2.1'

        cfg.VIPS_ENGINE_MIN_PIXELS = 20000000

        cfg.PROXY_ENGINE_ENGINES = [
            ('wikimedia_thumbor.engine.svg', ['svg']),
            ('wikimedia_thumbor.engine.xcf', ['xcf']),
            ('wikimedia_thumbor.engine.djvu', ['djvu']),
            ('wikimedia_thumbor.engine.vips', ['tiff', 'png']),
            ('wikimedia_thumbor.engine.tiff', ['tiff']),
            ('wikimedia_thumbor.engine.ghostscript', ['pdf']),
            ('wikimedia_thumbor.engine.gif', ['gif']),
            ('wikimedia_thumbor.engine.imagemagick', ['jpg', 'png']),
        ]

        cfg.FILTERS = [
            'wikimedia_thumbor.filter.conditional_sharpen',
            'wikimedia_thumbor.filter.format',
            'wikimedia_thumbor.filter.lang',
            'wikimedia_thumbor.filter.page',
            'wikimedia_thumbor.filter.crop',
            'wikimedia_thumbor.filter.flip',
            'thumbor.filters.quality',
            'thumbor.filters.rotate'
        ]

        return cfg

    def get_app(self):
        server_params = ServerParameters(None, None, None, None, None, None)

        cfg = self.get_config()

        importer = Importer(cfg)
        importer.import_modules()
        self.ctx = Context(server_params, cfg, importer)
        application = App(self.ctx)

        return application

    def run_and_check_ssim_and_size(
        self,
        url,
        expected,
        expected_ssim,
        size_tolerance
    ):
        """Request URL and check ssim and size.

        Arguments:
        url -- thumbnail URL
        expected -- reference thumbnail file
        expected_ssim -- minimum SSIM score
        size_tolerance -- maximum file size ratio between reference and result
        exif_fields -- expected EXIF field values
        """
        try:
            result = self.retrieve("/%s" % url)
        except Exception as e:
            assert False, 'Exception occured: %r' % e

        assert result is not None, 'No result'
        assert result.code == 200, 'Response code: %s' % result.code

        generated = Image.open(result.buffer)

        expected_path = os.path.join(
            os.path.dirname(__file__),
            'thumbnails',
            expected
        )
        expected = Image.open(expected_path).convert(generated.mode)

        heights = (generated.size[1], expected.size[1])
        assert abs(generated.size[1] - expected.size[1]) <= 1, \
            'Height differs too much: %d %d\n' % heights

        widths = (generated.size[0], expected.size[0])
        assert abs(generated.size[0] - expected.size[0]) <= 1, \
            'Width differs too much: %d %d\n' % widths

        ssim = compute_ssim(generated, expected)

        assert ssim >= expected_ssim, 'Images too dissimilar: %f\n' % ssim

        expected_filesize = os.path.getsize(expected_path)
        generated_filesize = len(result.buffer.getvalue())

        sizes = (generated_filesize, expected_filesize)
        assert generated_filesize <= expected_filesize * size_tolerance, \
            'Generated file bigger than size tolerance: %d vs %d ' % sizes

        return generated
