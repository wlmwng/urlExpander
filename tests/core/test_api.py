import os

import pytest
from urlexpander.core.api import expand, expand_with_content


@pytest.fixture
def urls():
    urls = [
        "https://trib.al/xXI5ruM",
        "https://www.youtube.com/watch?v=8NwKcfXvGl4",
        "https://t.co/KOwxFeoICW?amp=1",
        "http://feedproxy.google.com/~r/breitbart/~3/bh9JQvQPihk/",
        "https://t.co/zNU1eHhQRn",
    ]
    yield urls


@pytest.fixture
def resolved_urls():
    resolved_urls = [
        "https://www.breitbart.com/clips/2017/12/31/lindsey-graham-trump-just-cant-tweet-iran/",
        "https://www.youtube.com/watch?v=8NwKcfXvGl4",
        "https://www.cnn.com/2021/10/05/us/california-oil-spill-tuesday/index.html?utm_content=2021-10-06T00%3A16%3A08&utm_source=twCNN&utm_medium=social&utm_term=link",
        "https://www.breitbart.com/radio/2017/08/15/raheem-kassam-no-go-zones-statue-destruction-muslim-migration-left-wants-erase-america/?utm_source=feedburner&utm_medium=feed&utm_campaign=Feed%3A+breitbart+%28Breitbart+News%29",
        "https://www.nfib.com/content/press-release/elections/small-business-endorses-shuster-for-reelection-73730/?utm_campaign=Advocacy&utm_source=Twitter&utm_medium=Social",
    ]
    yield resolved_urls


class TestExpand(object):
    def test_one_url(self, urls, resolved_urls):
        assert resolved_urls[0] == expand(urls[0])

    def test_many_urls(self, urls, resolved_urls):
        assert resolved_urls == expand(urls, use_head=False)

    def test_caching(self, urls, resolved_urls, tmpdir):
        assert resolved_urls == expand(
            urls, cache_file=os.path.join(tmpdir, "__cache.json")
        )
        assert resolved_urls == expand(
            urls, cache_file=os.path.join(tmpdir, "__cache.json")
        )


class TestExpandWithContent(object):
    def test_one_url(self, urls, resolved_urls):
        data = expand_with_content(urls[0])
        assert data["original_url"] == urls[0]
        assert isinstance(data["response_url"], str)
        assert data["resolved_url"] == resolved_urls[0]
        assert isinstance(data["resolved_domain"], str)
        assert isinstance(data["response_code"], int)
        assert isinstance(data["response_reason"], str)
        assert "<!DOCTYPE html>" in data["resolved_text"]
