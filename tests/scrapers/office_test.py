"""
Tests for Office scraper.

This module tests that:
    - MIME type, version, streams and well-formedness of well-formed office
      files (odt, doc, docx, odp, ppt, pptx, ods, xsl, xlsx, odg and odf) are
      determined correctly and without anything recorded in scraper errors.
    - MIME type, version, streams and well-formedness of corrupted office
      files are determined correctly with 'source file could not be loaded'
      being recorded in scraper errors.
    - Without well-formedness check, scraper messages contain 'Skipping
      scraper' and well_formed is None
    - With well-formedness check, the following MIME type and version
      combinations are supported:
        - application/vnd.oasis.opendocument.text, 1.1
        - application/msword, 11.0
        - application/vnd.openxmlformats-officedocument.wordprocessingml.document,
          15.0
        - application/vnd.oasis.opendocument.presentation, 1.1
        - application/vnd.ms-powerpoint, 11.0
        - application/vnd.openxmlformats-officedocument.presentationml.presentation,
          15.0
        - application/vnd.oasis.opendocument.spreadsheet, 1.1
        - application/vnd.ms-excel, 11.0
        - application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,
          15.0
        - application/vnd.oasis.opendocument.graphics, 1.1
        - application/vnd.oasis.opendocument.formula, 1.0
    - These MIME types are also supported with a made up version or None as
      the version.
    - A made up MIME type is not supported.
    - Without well-formedness check, none of these MIME types are supported.
    - Forcing MIME type and/or version works.
"""
from __future__ import unicode_literals

import os
from multiprocessing import Pool

import pytest
import six

from file_scraper.office.office_scraper import OfficeScraper
from tests.common import (parse_results, force_correct_filetype,
                          partial_message_included)

BASEPATH = "tests/data"


@pytest.mark.parametrize(
    ["filename", "mimetype"],
    [
        ("valid_1.1.odt", "application/vnd.oasis.opendocument.text"),
        ("valid_11.0.doc", "application/msword"),
        ("valid_15.0.docx", "application/vnd.openxmlformats-"
         "officedocument.wordprocessingml.document"),
        ("valid_1.1.odp",
         "application/vnd.oasis.opendocument.presentation"),
        ("valid_11.0.ppt", "application/vnd.ms-powerpoint"),
        ("valid_15.0.pptx", "application/vnd.openxml"
         "formats-officedocument.presentationml.presentation"),
        ("valid_1.1.ods",
         "application/vnd.oasis.opendocument.spreadsheet"),
        ("valid_11.0.xls", "application/vnd.ms-excel"),
        ("valid_15.0.xlsx", "application/vnd."
         "openxmlformats-officedocument.spreadsheetml.sheet"),
        ("valid_1.1.odg", "application/vnd.oasis.opendocument.graphics"),
        ("valid_1.0.odf", "application/vnd.oasis.opendocument.formula"),
    ]
)
def test_scraper_valid_file(filename, mimetype, evaluate_scraper):
    """Test valid files with scraper."""
    result_dict = {
        "purpose": "Test valid file.",
        "stdout_part": "",
        "stderr_part": ""}
    correct = parse_results(filename, mimetype,
                            result_dict, True)
    scraper = OfficeScraper(correct.filename, True, correct.params)
    scraper.scrape_file()
    correct.streams[0]["version"] = "(:unav)"
    correct.streams[0]["mimetype"] = "(:unav)"

    evaluate_scraper(scraper, correct, False)
    assert scraper.messages()
    assert not scraper.errors()


@pytest.mark.parametrize(
    ["filename", "mimetype"],
    [
        ("invalid_1.1_corrupted.odt", "application/vnd.oasis.opendocument"
         ".text"),
        ("invalid_15.0_corrupted.docx", "application/vnd.openxmlformats-"
         "officedocument.wordprocessingml.document"),
        ("invalid_1.1_corrupted.odp",
         "application/vnd.oasis.opendocument.presentation"),
        ("invalid_15.0_corrupted.pptx", "application/vnd.openxml"
         "formats-officedocument.presentationml.presentation"),
        ("invalid_1.1_corrupted.ods",
         "application/vnd.oasis.opendocument.spreadsheet"),
        ("invalid_15.0_corrupted.xlsx", "application/vnd."
         "openxmlformats-officedocument.spreadsheetml.sheet"),
        ("invalid_1.1_corrupted.odg", "application/vnd.oasis.opendocument"
         ".graphics"),
        ("invalid_1.0_corrupted.odf", "application/vnd.oasis.opendocument"
         ".formula"),
    ]
)
def test_scraper_invalid_file(filename, mimetype, evaluate_scraper):
    """Test scraper with invalid files."""
    result_dict = {
        "purpose": "Test invalid file.",
        "stdout_part": "",
        "stderr_part": "source file could not be loaded"}
    correct = parse_results(filename, mimetype, result_dict, True)
    scraper = OfficeScraper(correct.filename, True, correct.params)
    scraper.scrape_file()
    correct.streams[0]["version"] = "(:unav)"
    correct.streams[0]["mimetype"] = "(:unav)"

    evaluate_scraper(scraper, correct)


def _scrape(filename, mimetype):
    scraper = OfficeScraper(os.path.join(BASEPATH, mimetype.replace("/", "_"),
                                         filename))
    scraper.scrape_file()
    return scraper.well_formed


@pytest.mark.parametrize(
    ["filename", "mimetype"],
    [
        ("valid_1.1.odt", "application/vnd.oasis.opendocument.text"),
    ]
)
def test_parallel_validation(filename, mimetype):
    """
    Test validation in parallel.

    This is done because Libreoffice convert command is prone for
    freezing which would cause TimeOutError here.
    """

    number = 3
    pool = Pool(number)
    results = [pool.apply_async(_scrape, (filename, mimetype))
               for _ in range(number)]

    for result in results:
        assert result.get(timeout=5)


def test_no_wellformed():
    """Test scraper without well-formed check."""
    scraper = OfficeScraper("tests/data/application_msword/valid_11.0.doc",
                            False)
    scraper.scrape_file()
    assert partial_message_included("Skipping scraper", scraper.messages())
    assert scraper.well_formed is None


@pytest.mark.parametrize(
    ["mime", "ver"],
    [
        ("application/vnd.oasis.opendocument.text", "1.1"),
        ("application/msword", "11.0"),
        ("application/vnd.openxmlformats-"
         "officedocument.wordprocessingml.document", "15.0"),
        ("application/vnd.oasis.opendocument.presentation", "1.1"),
        ("application/vnd.ms-powerpoint", "11.0"),
        ("application/vnd.openxml"
         "formats-officedocument.presentationml.presentation", "15.0"),
        ("application/vnd.oasis.opendocument.spreadsheet", "1.1"),
        ("application/vnd.ms-excel", "11.0"),
        ("application/vnd."
         "openxmlformats-officedocument.spreadsheetml.sheet", "15.0"),
        ("application/vnd.oasis.opendocument.graphics", "1.1"),
        ("application/vnd.oasis.opendocument.formula", "1.0"),
    ]
)
def test_is_supported(mime, ver):
    """Test is_supported method."""
    assert OfficeScraper.is_supported(mime, ver, True)
    assert OfficeScraper.is_supported(mime, None, True)
    assert not OfficeScraper.is_supported(mime, ver, False)
    assert OfficeScraper.is_supported(mime, "foo", True)
    assert not OfficeScraper.is_supported("foo", ver, True)


@pytest.mark.parametrize(
    ["result_dict", "filetype"],
    [
        ({"purpose": "Test forcing correct MIME type and version",
          "stdout_part": "MIME type and version not scraped, using",
          "stderr_part": ""},
         {"given_mimetype": "application/vnd.oasis.opendocument.spreadsheet",
          "given_version": "1.1",
          "expected_mimetype": "application/vnd.oasis.opendocument.spreadsheet",
          "expected_version": "1.1"}),
        ({"purpose": "Test forcing correct MIME type",
          "stdout_part": "MIME type not scraped, using",
          "stderr_part": ""},
         {"given_mimetype": "application/vnd.oasis.opendocument.spreadsheet",
          "given_version": None,
          "expected_mimetype": "application/vnd.oasis.opendocument.spreadsheet",
          "expected_version": "(:unav)"}),
        ({"purpose": "Test forcing version only (no effect)",
          "stdout_part": "",
          "stderr_part": ""},
         {"given_mimetype": None, "given_version": "1.1",
          "expected_mimetype": "(:unav)", "expected_version": "(:unav)"}),
        ({"purpose": "Test forcing wrong MIME type",
          "stdout_part": "MIME type not scraped, using",
          "stderr_part": "is not supported"},
         {"given_mimetype": "unsupported/mime", "given_version": None,
          "expected_mimetype": "unsupported/mime",
          "expected_version": "(:unav)"})
    ]
)
def test_forced_filetype(result_dict, filetype, evaluate_scraper):
    """
    Test using user-supplied MIME-types and versions.
    """
    filetype[six.text_type("correct_mimetype")] = "application/vnd.oasis.opendocument.spreadsheet"
    correct = force_correct_filetype("valid_1.1.ods", result_dict,
                                     filetype, ["(:unav)"])

    params = {"mimetype": filetype["given_mimetype"],
              "version": filetype["given_version"]}
    scraper = OfficeScraper(correct.filename, True, params)
    scraper.scrape_file()

    evaluate_scraper(scraper, correct)
