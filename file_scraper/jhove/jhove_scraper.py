"""Scraper for gif, html, jpeg, tif, pdf and wav files using JHove."""

try:
    import lxml.etree
except ImportError:
    pass

from file_scraper.base import BaseScraper, Shell
from file_scraper.jhove.jhove_model import (JHoveGifMeta, JHoveHtmlMeta,
                                            JHoveJpegMeta, JHoveTiffMeta,
                                            JHovePdfMeta, JHoveWavMeta,
                                            get_field)
from file_scraper.utils import ensure_str


class JHoveScraperBase(BaseScraper):
    """Scraping methods for all specific JHove scrapers."""

    _supported_metadata = []
    _jhove_module = None

    def __init__(self, filename, check_wellformed=True, params=None):
        """
        Initialize JHove base scarper.

        :filename: File path
        :check_wellformed: True for the full well-formed check, False for just
                           detection and metadata scraping
        :params: Extra parameters needed for the scraper
        """
        self._report = None  # JHove report
        self._shell = None  # Shell object
        super(JHoveScraperBase, self).__init__(filename, check_wellformed,
                                               params)

    def scrape_file(self):
        """Run JHove command and store XML output to self.report."""
        if not self._check_wellformed and self._only_wellformed:
            self._messages.append("Skipping scraper: Well-formed check not"
                                  "used.")
            return

        exec_cmd = ["jhove", "-h", "XML", "-m",
                    self._jhove_module, self.filename]
        self._shell = Shell(exec_cmd)

        if self._shell.returncode != 0:
            self._errors.append("JHove returned error: %s\n%s" % (
                self._shell.returncode, self._shell.stderr))

        self._report = lxml.etree.fromstring(self._shell.stdout)

        status = get_field(self._report, "status")
        self._messages.append(status)
        if "Well-Formed and valid" not in status:
            self._errors.append("Validator returned error: %s\n%s" % (
                ensure_str(self._shell.stdout),
                ensure_str(self._shell.stderr)
            ))

        for md_class in self._supported_metadata:
            if md_class.is_supported(get_field(self._report, "mimeType")):
                self.streams.append(md_class(self._report, self._errors))

        self._check_supported()


class JHoveGifScraper(JHoveScraperBase):
    """Variables for scraping gif files."""

    _jhove_module = "GIF-hul"
    _supported_metadata = [JHoveGifMeta]


class JHoveHtmlScraper(JHoveScraperBase):
    """Variables for scraping html files."""

    _jhove_module = "HTML-hul"
    _supported_metadata = [JHoveHtmlMeta]


class JHoveJpegScraper(JHoveScraperBase):
    """Variables for scraping jpeg files."""

    _jhove_module = "JPEG-hul"
    _supported_metadata = [JHoveJpegMeta]


class JHoveTiffScraper(JHoveScraperBase):
    """Variables for scraping tiff files."""

    _jhove_module = "TIFF-hul"
    _supported_metadata = [JHoveTiffMeta]


class JHovePdfScraper(JHoveScraperBase):
    """Variables for scraping pdf files."""

    _jhove_module = "PDF-hul"
    _supported_metadata = [JHovePdfMeta]


class JHoveWavScraper(JHoveScraperBase):
    """Variables for scraping wav files."""

    _jhove_module = "WAVE-hul"
    _supported_metadata = [JHoveWavMeta]
