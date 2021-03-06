"""PDF/A metadata model."""
from __future__ import unicode_literals

from file_scraper.base import BaseMeta
from file_scraper.utils import metadata


class VerapdfMeta(BaseMeta):
    """Metadata model for PDF/A."""

    # Supported mimetypes and versions
    _supported = {"application/pdf": ["A-1a", "A-1b", "A-2a", "A-2b", "A-2u",
                                      "A-3a", "A-3b", "A-3u"]}

    def __init__(self, profile, mimetype=None, version=None):
        """
        Initialize the metadata model.

        :profile: profileName from verapdf report
        """
        self._profile = profile
        super(VerapdfMeta, self).__init__(mimetype, version)

    @metadata()
    def mimetype(self):
        if self._given_mimetype:
            return self._given_mimetype
        return "application/pdf"

    @metadata(important=True)
    def version(self):
        """
        Return the version based on the profile given to the constructor.

        For files that are not PDF/A, other scrapers need to be used to
        determine the version.
        """
        if self._given_mimetype and self._given_version:
            return self._given_version
        return "A" + self._profile.split("PDF/A")[1].split(
            " validation profile")[0].lower()

    # pylint: disable=no-self-use
    @metadata()
    def stream_type(self):
        """Return file type."""
        return "binary"
