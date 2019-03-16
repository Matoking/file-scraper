"""Scraper for CSV file formats
"""
import csv

from file_scraper.base import BaseScraper


class Csv(BaseScraper):
    """Scraper for CSV files.
    """

    _supported = {'text/csv': ['']}  # Supported mimetype
    _allow_versions = True           # Allow any version 

    def __init__(self, filename, mimetype, validation=True, params=None):
        """Initialize for delimiter and separator info.
        :filename: File path
        :mimetype: Predicted mimetype of the file
        :validation: True for the full validation, False for just
                     identification and metadata scraping
        :params: Extra parameters: delimiter and separator
        """
        if params is None:
            params = {}
        self._csv_delimiter = params.get('delimiter', None)
        self._csv_separator = params.get('separator', None)
        self._csv_fields = params.get('fields', [])
        self._csv_first_line = None
        super(Csv, self).__init__(filename, mimetype, validation, params)

    def scrape_file(self):
        """Scrape CSV file.
        """
        if self._csv_fields is None:
            self._csv_fields = []
        try:
            with open(self.filename, 'rb') as csvfile:
                reader = csv.reader(csvfile)
                csvfile.seek(0)
                dialect = csv.Sniffer().sniff(csvfile.read(1024))
                if not self._csv_delimiter:
                    self._csv_delimiter = dialect.delimiter
                if not self._csv_separator:
                    self._csv_separator = dialect.lineterminator
                csv.register_dialect('new_dialect',
                                     delimiter=self._csv_delimiter,
                                     lineterminator=self._csv_separator,
                                     strict=True,
                                     doublequote=True)

                csvfile.seek(0)
                reader = csv.reader(csvfile, dialect='new_dialect')
                self._csv_first_line = reader.next()

                if len(self._csv_fields) > 0 and \
                        len(self._csv_fields) != len(self._csv_first_line):
                    self.errors(
                        "CSV validation error: field counts in the given "
                        "header parameter and the CSV header don't match."
                    )
                    return

                for _ in reader:
                    pass

        except csv.Error as exception:
            self.errors("CSV error on line %s: %s" %
                        (reader.line_num, exception))
        else:
            self.messages("CSV file was scraped successfully.")
        finally:
            self._check_supported()
            self._collect_elements()

    def _s_version(self):
        """Return version
        """
        return ''

    def _s_delimiter(self):
        """Return delimiter
        """
        return self._csv_delimiter

    def _s_separator(self):
        """Return separator
        """
        return self._csv_separator

    def _s_first_line(self):
        """Return first line
        """
        return self._csv_first_line

    # pylint: disable=no-self-use
    def _s_stream_type(self):
        """Return file type
        """
        return 'text'