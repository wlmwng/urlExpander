from urlexpander.core import constants, datasets, html_utils, tweet_utils, url_utils

from urlexpander.core.api import expand, expand_with_content

from urlexpander.extended.news_api import (
    request_active_url,
    request_archived_url,
    fetch_url,
    fetch_urls,
    fetch_urls_to_file,
    load_fetched_from_file,
)

__version__ = "0.0.38"
__author__ = "Leon Yin"
