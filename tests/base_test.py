"""
Tests for scraper base.

This module tests:
    - Shell command execution.
    - That is_supported() method returns correct values for a variety of
      mimetypes and versions.
    - That messages and errors are returned properly.
    - That scraper attributes and well_formed property are set and retrieved
      correctly
    - That overriding MIME type and/or version scraping by giving them as
      parameters is possible, but giving version without MIME type has no
      effect.
"""
from __future__ import unicode_literals

import pytest

from file_scraper.base import BaseScraper, BaseMeta, BaseDetector
from file_scraper.utils import metadata
from tests.common import partial_message_included


class BaseMetaBasic(BaseMeta):
    """Metadata model supporting specific versions of one MIME type"""

    _supported = {"test/mimetype": ["0.1", "0.2"]}


class BaseScraperBasic(BaseScraper):
    """
    A very basic scraper for only specific versions of one MIME type.

    This scraper allows only one specific version in is_supported()
    and is used for metadata collection.
    """

    _supported_metadata = [BaseMetaBasic]

    def scrape_file(self):
        """Do nothing, scraping not needed here."""
        self.streams.append(BaseMetaBasic(self._params.get("mimetype", None),
                                          self._params.get("version", None)))


class BaseMetaVersion(BaseMeta):
    """Basic metadata model supporting all versions of a single MIME type."""

    _allow_versions = True
    _supported = {"test/mimetype": []}


class BaseScraperVersion(BaseScraperBasic):
    """
    A very basic scraper for multiple versions.

    This scraper that allows any given version in is_supported()
    and is used for metadata collection
    """

    _supported_metadata = [BaseMetaVersion]


class BaseScraperWellFormed(BaseScraperBasic):
    """Scraper that allows only scraping for well_formed result."""

    _only_wellformed = True


class BaseDetectorBasic(BaseDetector):
    """Basic detector."""

    # pylint: disable=too-few-public-methods
    def detect(self):
        pass


@pytest.mark.parametrize(
    ["scraper_class", "mimetype", "version", "check_wellformed", "supported"],
    [
        (BaseScraperBasic, "test/mimetype", "0.1", True, True),
        (BaseScraperBasic, "test/mimetype", None, True, True),
        (BaseScraperBasic, "test/mimetype", "0.1", False, True),
        (BaseScraperBasic, "test/notsupported", "0.1", True, False),
        (BaseScraperBasic, "test/mimetype", "X", True, False),
        (BaseScraperVersion, "test/mimetype", "0.1", True, True),
        (BaseScraperVersion, "test/mimetype", None, True, True),
        (BaseScraperVersion, "test/mimetype", "0.1", False, True),
        (BaseScraperVersion, "test/notsupported", "0.1", True, False),
        (BaseScraperVersion, "test/mimetype", "X", True, True),
        (BaseScraperWellFormed, "test/mimetype", "0.1", True, True),
        (BaseScraperWellFormed, "test/mimetype", None, True, True),
        (BaseScraperWellFormed, "test/mimetype", "0.1", False, False),
        (BaseScraperWellFormed, "test/notsupported", "0.1", False, False),
        (BaseScraperWellFormed, "test/mimetype", "X", True, False),
    ]
)
def test_is_supported(scraper_class, mimetype, version, check_wellformed,
                      supported):
    """Test scraper's is_supported() method."""
    assert (scraper_class.is_supported(mimetype, version, check_wellformed) ==
            supported)


def test_messages_errors():
    """Test scraper's messages and errors."""
    scraper = BaseScraperBasic("testfilename", "test/mimetype")
    # pylint: disable=protected-access
    scraper._messages.append("test message")
    scraper._messages.append("test message 2")
    scraper._messages.append("")
    scraper._errors.append("test error")
    scraper._errors.append("test error 2")
    assert scraper.messages() == ["test message", "test message 2"]
    assert scraper.errors() == ["test error", "test error 2"]


def test_scraper_properties():
    """Test scraper's attributes and well_formed property."""
    scraper = BaseScraperBasic("testfilename", True, {"test": "value"})
    # pylint: disable=protected-access
    scraper._messages.append("success")
    assert scraper.well_formed
    scraper._errors.append("error")
    assert not scraper.well_formed

    assert scraper.filename == "testfilename"
    # pylint: disable=protected-access
    assert scraper._check_wellformed
    assert scraper._params == {"test": "value"}

    scraper = BaseScraperBasic("testfilename", False)
    scraper._messages.append("success")
    assert scraper.well_formed is None
    scraper._errors.append("error")
    assert scraper.well_formed is None


@pytest.mark.parametrize(
    ["given_mimetype", "given_version", "expected_mimetype",
     "expected_version", "expected_message"],
    [
        (None, None, "(:unav)", "(:unav)", None),
        ("test/override", "99.9", "test/override", "99.9",
         "MIME type and version not scraped, using user-supplied"),
        ("test/override", None, "test/override", "(:unav)",
         "MIME type not scraped, using user-supplied value."),
        (None, "99.9", "(:unav)", "(:unav)", None)
    ]
)
def test_overriding_filetype(given_mimetype, given_version, expected_mimetype,
                             expected_version, expected_message):
    """
    Test forcing the base scraper to use certain MIME type and/or version.
    """
    scraper = BaseScraperBasic("testfilename",
                               params={"mimetype": given_mimetype,
                                       "version": given_version})
    scraper.scrape_file()
    assert scraper.streams[0].mimetype() == expected_mimetype
    assert scraper.streams[0].version() == expected_version
    if expected_message:
        assert partial_message_included(expected_message, scraper.messages())
    else:
        assert not scraper.messages()


class BaseMetaCustom(BaseMeta):
    """Metadata model that uses MIME type and version given to constructor."""

    _supported = {"test/mimetype": ["0.1"]}

    def __init__(self, mimetype, version):
        super(BaseMetaCustom, self).__init__(mimetype, version)
        self._mimetype = mimetype
        self._version = version

    @metadata()
    def mimetype(self):
        return self._mimetype

    @metadata()
    def version(self):
        return self._version


class BaseScraperSupported(BaseScraper):
    """Basic scraper using BaseMetaCustom metadata model."""

    _supported_metadata = [BaseMetaCustom]


@pytest.mark.parametrize(
    ["scraper_class", "mimetype", "version", "errors"],
    [
        (BaseScraperSupported, "test/mimetype", "0.1", None),
        (BaseScraperBasic, "test/mimetype", None,
         "type test/mimetype with version None is not supported"),
        (BaseScraperBasic, "test/mimetype", "0.0",
         "type test/mimetype with version 0.0 is not supported"),
        (BaseScraperBasic, "test/falsemime", "0.1",
         "type test/falsemime with version 0.1 is not supported"),
        (BaseScraperBasic, None, "0.1",
         "None is not a supported MIME type")
    ]
)
def test_check_supported(scraper_class, mimetype, version, errors):
    """Test scraper's _check_supported() method."""
    # pylint: disable=protected-access
    scraper = scraper_class("testfilename", mimetype)
    scraper.streams.append(BaseMetaCustom(mimetype, version))
    scraper._check_supported()
    if not errors:
        assert not scraper.errors()
    else:
        assert partial_message_included(errors, scraper.errors())


def test_base_detector():
    """Test base detector."""
    detector = BaseDetectorBasic("testfilename")
    assert detector.filename == "testfilename"
