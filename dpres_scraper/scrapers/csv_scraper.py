"""Scraper for CSV file formats
"""
import csv

from dpres_scraper.base import BaseScraper


class Csv(BaseScraper):
    """Scraper for CSV files
    """

    _supported = {'text/csv': []}

    def __init__(self, mimetype, filename, validation):
        """Initialize for delimiter and separator info
        """
        self._csv_delimiter = None
        self._csv_separator = None
        super(Csv, self).__init__(mimetype, filename, validation)

    def scrape_file(self):
        """Scrape CSV file
        """
        try:
            with open(self.filename, 'rb') as csvfile:
                reader = csv.reader(csvfile)
                first_line = reader.next()
                sniffer = csv.Sniffer()
                dialect = sniffer.sniff(first_line)
                self._csv_delimiter = dialect.delimiter
                self._csv_separator = dialect.lineterminator
                for _ in reader:
                    pass
        except csv.Error as exception:
            self.errors("CSV error on line %s: %s" %
                        (reader.line_num, exception))
        else:
            self.messages("File was scraped successfully.")
        finally:
            self._collect_elements()


    def _s_delimiter(self):
        """Return delimiter
        """
        return self._csv_delimiter

    def _s_separator(self):
        """Return separator
        """
        return self._csv_separator

    # pylint: disable=no-self-use
    def _s_stream_type(self):
        """Return file type
        """
        return 'char'
