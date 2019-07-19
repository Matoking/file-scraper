"""File metadata scraper."""
from __future__ import unicode_literals

from file_scraper.dummy.dummy_scraper import FileExists
from file_scraper.iterator import iter_detectors, iter_scrapers
from file_scraper.jhove.jhove_scraper import JHoveUtf8Scraper
from file_scraper.textfile.textfile_scraper import TextfileScraper
from file_scraper.utils import encode_path, generate_metadata_dict, hexdigest

LOSE = (None, "(:unav)")


class Scraper(object):
    """File indentifier and scraper."""

    # pylint: disable=no-member, too-many-instance-attributes

    def __init__(self, filename, **kwargs):
        """Initialize scraper.
        :filename: File path
        :kwargs: Extra arguments for certain scrapers
        """
        if filename is not None:
            filename = encode_path(filename)
        self.filename = filename
        self.mimetype = None
        self.version = None
        self.streams = None
        self.well_formed = None
        self.info = None
        self._params = kwargs
        self._scraper_results = []

    def _identify(self):
        """Identify file format and version."""
        self.info = {}
        for detector in iter_detectors():
            tool = detector(self.filename)
            tool.detect()
            self.info[len(self.info)] = tool.info
            important = tool.get_important()
            if self.mimetype in LOSE:
                self.mimetype = tool.mimetype
            if self.mimetype == tool.mimetype and \
                    self.version in LOSE:
                self.version = tool.version
            if "mimetype" in important and \
                    important["mimetype"] is not None:
                self.mimetype = important["mimetype"]
            if "version" in important and \
                    important["version"] is not None:
                self.mimetype = important["version"][self.mimetype]

    def _scrape_file(self, scraper):
        """Scrape with the given scraper.
        :scraper: Scraper instance
        """
        scraper.scrape_file()
        if scraper.streams:
            self._scraper_results.append(scraper.streams)
        self.info[len(self.info)] = scraper.info()
        if scraper.well_formed is not None:
            if self.well_formed in [None, True]:
                self.well_formed = scraper.well_formed

    def _check_utf8(self, check_wellformed):
        """
        UTF-8 check only for UTF-8.

        We know the charset after actual scraping.
        """
        if "charset" in self.streams[0] and \
                self.streams[0]["charset"] == "UTF-8":
            scraper = JHoveUtf8Scraper(self.filename, check_wellformed)
            self._scrape_file(scraper)

    def _check_mimetype_version(self):
        """
        Detect the MIME type and version.

        Ideally the MIME type and version from the scraper are used, but if
        they are not used, values supplied by the detector are used.
        """
        if self.streams[0]["mimetype"] not in LOSE:
            self.mimetype = self.streams[0]["mimetype"]
        else:
            self.streams[0]["mimetype"] = self.mimetype
        if self.streams[0]["version"] not in LOSE:
            self.version = self.streams[0]["version"]
        elif self.version:
            self.streams[0]["version"] = self.version

    def scrape(self, check_wellformed=True):
        """Scrape file and collect metadata.
        :check_wellformed: True, full scraping; False, skip well-formed check.
        """
        self.streams = None
        self.info = {}
        self.well_formed = None

        file_exists = FileExists(self.filename, None)
        self._scrape_file(file_exists)

        if file_exists.well_formed is False:
            self.streams = {}
            return

        self._identify()
        self._params["mimetype"] = self.mimetype
        for scraper_class in iter_scrapers(
                mimetype=self.mimetype, version=self.version,
                check_wellformed=check_wellformed, params=self._params):
            scraper = scraper_class(self.filename, check_wellformed,
                                    self._params)
            self._scrape_file(scraper)
        self.streams = generate_metadata_dict(self._scraper_results, LOSE)
        self._check_utf8(check_wellformed)
        self._check_mimetype_version()

    def is_textfile(self):
        """Find out if file is a text file.
        :returns: True, if file is a text file, false otherwise
        """
        scraper = TextfileScraper(self.filename, self.mimetype)
        scraper.scrape_file()
        return scraper.well_formed

    def checksum(self, algorithm="MD5"):
        """Return the checksum of the file with given algorithm.
        :algorithm: MD5 or SHA variant
        :returns: Calculated checksum
        """
        return hexdigest(self.filename, algorithm)
