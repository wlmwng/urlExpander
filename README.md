# urlExpander

[![PyPI](https://img.shields.io/pypi/l/urlexpander.svg)](https://github.com/wlmwng/urlExpander/blob/master/LICENSE)

[urlExpander](https://github.com/SMAPPNYU/urlExpander) is a Python package by NYU's Social Media and Political Participation Lab. It is intended for social media researchers who are interested in analyzing URLs. This fork of urlExpander focuses on scraping online news articles and collecting the URLs associated with them.

## About
As noted in the original package, analytics and ad-based services complicate URL analysis by obfuscating the destination of shortened URLs. To address this challenge, urlExpander sends an HTTP request for each shortened URL and returns the URL's expanded version to the user. This fork builds on the existing functionality in two ways:

### 1. News article extraction 
When urlExpander sends an HTTP GET request, the server responds with both the expanded URL as well as the HTML of the webpage. This fork makes use of the returned HTML by extracting the main text of the news article using [news-please](https://github.com/fhamborg/news-please).

It is not uncommon for webpages associated with URLs to be moved or taken offline. To increase the chance of retrieving a URL's article text, this fork's `fetch_url()` function first tries to extract the article text from a direct server response. If this initial attempt returns an error, a fallback option checks if the article text can be extracted from an archived version of the webpage using [waybackpy](https://github.com/akamhy/waybackpy) (a Python interface for the Internet Archive's Wayback Machine API).

### 2. URL standardization

In addition to shortening URLs, analytics and ad-based services can add a variety of URL parameters to track where traffic is coming from. While this information is useful for understanding user engagement, this often results in multiple URLs leading to the same news article. To reduce unnecessary variation, this fork standardizes the expanded URL with the help of [w3lib](https://github.com/scrapy/w3lib) and [urllib.parse](https://docs.python.org/3/library/urllib.parse.html#module-urllib.parse) (caution: while the standardized URL will likely lead to the same/similar webpage as the unmodified URL, this isn't guaranteed).





## Installation

After cloning the repository, run:

```
pip install .
```
or
```
# editable mode
pip install -e . 
```

## Quick Start

### URL expansion only
```
import urlexpander
urlexpander.expand('https://trib.al/xXI5ruM')
```
returns
```
'https://www.breitbart.com/video/2017/12/31/lindsey-graham-trump-just-cant-tweet-iran/'
```
The function shines given a massive list of urls to unshorten:
```
resolved_urls = urlexpander.expand(list_of_short_urls, 
                                    chunksize=1280, 
                                    n_workers=8,
                                    cache_file='tmp.json')
```
\**urlExpander can expand multiple URLs in parallel using multithreading. When setting the number of threads (`n_workers`), consider how frequently a domain will be requested to avoid hitting server limits. Note that this version of urlExpander adds a minimum delay of 8 seconds before sending each request (the delay time can be adjusted in [constants.py](https://github.com/wlmwng/urlExpander/blob/news_api/urlexpander/core/constants.py)).*


### News article extraction + URL expansion + URL standardization

The `urls` argument of `fetch_urls()` accepts a dictionary or a list of dictionaries. The only required key in each dictionary is `url`. Extra key-value pairs can be added if you want to pass along information to the output.

```
import urlexpander

examples = [
    {"url": "http://feedproxy.google.com/~r/breitbart/~3/bh9JQvQPihk/"},
    {"url": "http://www.oann.com/pm-abe-to-send-message-japan-wont-repeat-war-atrocities-2/",
    "outlet": "One America News"}
]

fetch_generator = urlexpander.fetch_urls(
    urls=examples, fetch_function=urlexpander.fetch_url
)

# fetch the URLs and parse the content
fetched = [json.loads(r) for r in fetch_generator]

fetched[0]
```
Here is an example of the fetched content:
- `article_maintext` contains the extracted news article.
- `resolved_text` contains the webpage's HTML. This is useful as a backup option if news-please can't extract the article and you need to apply custom extraction logic.

```
{'article_maintext': [redacted],
 'original_url': 'http://feedproxy.google.com/~r/breitbart/~3/bh9JQvQPihk/',
 'resolved_url': 'https://www.breitbart.com/radio/2017/08/15/raheem-kassam-no-go-zones-statue-destruction-muslim-migration-left-wants-erase-america/?utm_source=feedburner&utm_medium=feed&utm_campaign=Feed%3A+breitbart+%28Breitbart+News%29',
 'resolved_domain': 'breitbart.com',
 'resolved_netloc': 'www.breitbart.com',
 'standardized_url': 'www.breitbart.com/radio/2017/08/15/raheem-kassam-no-go-zones-statue-destruction-muslim-migration-left-wants-erase-america',
 'is_generic_url': False,
 'response_code': 200,
 'response_reason': 'OK',
 'fetch_error': False,
 'resolved_text': [redacted],
 'FETCH_FUNCTION': 'request_active_url',
 'FETCH_AT': '2021-11-05T23:25:15.611729+00:00'}

```
The fetched content for each URL is returned as a JSON string. The content can be returned within your code or written to a .jsonl file. For a more detailed intro, check out the [News API](https://github.com/wlmwng/urlExpander/blob/news_api/examples/news_api.ipynb) Jupyter notebook!


## Acknowledgements
urlExpander was written by [Leon Yin](http://www.leonyin.org/) with contributions by Megan Brown, Nicole Baram and Gregory Eady for the [Social Media and Political Participation Lab at NYU](www.smappnyu.org). 

Please cite urlExpander in your publications if it helps your research. Here is an example BibTeX entry:

```
@misc{leon_yin_2018_1345144,
  author       = {Leon Yin},
  title        = {SMAPPNYU/urlExpander: Initial release},
  month        = aug,
  year         = 2018,
  doi          = {10.5281/zenodo.1345144},
  url          = {https://doi.org/10.5281/zenodo.1345144}
}
```