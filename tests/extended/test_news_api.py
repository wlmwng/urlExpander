import datetime
import json

import pytest
from urlexpander.extended.news_api import (
    NewsContent,
    fetch_url,
    fetch_urls,
    fetch_urls_to_file,
    load_fetched_from_file,
    request_active_url,
    request_archived_url,
)


@pytest.fixture
def dummy_url():
    dummy_url = "https://example.com"
    yield dummy_url


@pytest.fixture
def live_url():
    live_url = "http://feedproxy.google.com/~r/breitbart/~3/bh9JQvQPihk/"
    yield live_url


@pytest.fixture
def dead_url():
    dead_url = (
        "http://www.oann.com/pm-abe-to-send-message-japan-wont-repeat-war-atrocities-2/"
    )
    yield dead_url


@pytest.fixture
def nonarchived_url():
    nonarchived_url = "https://blog.reputationx.com/block-wayback-machine"
    yield nonarchived_url


class TestNewsContent(object):
    def test_init(self, dummy_url):
        """Check that basic instance is JSON serializable"""
        nc = NewsContent(dummy_url)
        nc_json = nc.to_json()
        assert isinstance(json.loads(nc_json), dict)

    def test_custom_key_str(self, dummy_url):
        """Check that custom kwargs are added to the output."""
        outlet = "CNN"
        nc = NewsContent(
            original_url=dummy_url,
            outlet=outlet,
        )
        nc_json = nc.to_json()
        nc_dict = json.loads(nc_json)
        assert outlet == nc_dict["outlet"]

    def test_datetime(self, dummy_url):
        """Check that to_json's CustomEncoder works for datetime types."""
        nc = NewsContent(dummy_url)
        nc_json = nc.to_json()
        json_dict = json.loads(nc_json)
        assert isinstance(
            datetime.datetime.fromisoformat(json_dict["FETCH_AT"]), datetime.datetime
        )

    def test_custom_key_dict(self, dummy_url):
        """Check that custom kwargs are added to the output and that to_json's CustomEncoder works for dictionaries."""
        themes = {"theme_1": "politics", "theme_2": "immigration"}
        nc = NewsContent(
            original_url=dummy_url,
            themes=themes,
        )
        nc_json = nc.to_json()
        nc_dict = json.loads(nc_json)
        assert themes == nc_dict["themes"]


class TestRequestActiveUrl(object):
    def test_live_url(self, live_url):
        """Request a URL which is actively served by the domain.
        This test will fail if 'live_url' doesn't exist anymore.
        """
        url = live_url
        req = request_active_url(url)
        nc = json.loads(req)

        # when newsplease fails to extract an article, it returns None
        assert isinstance(nc["article_maintext"], str) | (
            nc["article_maintext"] is None
        )
        assert nc["original_url"] == url
        assert (
            nc["resolved_url"]
            == "https://www.breitbart.com/radio/2017/08/15/raheem-kassam-no-go-zones-statue-destruction-muslim-migration-left-wants-erase-america/?utm_source=feedburner&utm_medium=feed&utm_campaign=Feed%3A+breitbart+%28Breitbart+News%29"
        )
        assert nc["resolved_domain"] == "breitbart.com"
        assert nc["resolved_netloc"] == "www.breitbart.com"
        assert (
            nc["standardized_url"]
            == "www.breitbart.com/radio/2017/08/15/raheem-kassam-no-go-zones-statue-destruction-muslim-migration-left-wants-erase-america"
        )
        assert nc["is_generic_url"] is False
        assert nc["response_code"] == 200
        assert nc["response_reason"] == "OK"
        assert nc["fetch_error"] is False
        assert "<!DOCTYPE html>" in nc["resolved_text"]
        assert nc["FETCH_FUNCTION"] == "request_active_url"
        assert isinstance(
            datetime.datetime.fromisoformat(nc["FETCH_AT"]), datetime.datetime
        )

    def test_dead_url(self, dead_url):
        """Check a URL which doesn't exist on the domain anymore."""
        url = dead_url
        req = request_active_url(url)
        nc = json.loads(req)
        assert nc["fetch_error"] is True


class TestRequestArchivedUrl(object):
    def test_archived_url(self, dead_url):
        """Check a URL which is archived by the Internet Archive's Wayback Machine.
        This test will fail if the URL is no longer hosted on the archive.
        """
        url = dead_url
        req = request_archived_url(url)
        nc = json.loads(req)

        # when newsplease fails to extract an article, it returns None
        assert isinstance(nc["article_maintext"], str) | (
            nc["article_maintext"] is None
        )
        assert nc["original_url"] == url
        assert (
            nc["resolved_url"]
            == "http://www.oann.com/pm-abe-to-send-message-japan-wont-repeat-war-atrocities-2/"
        )
        assert nc["resolved_domain"] == "oann.com"
        assert nc["resolved_netloc"] == "www.oann.com"
        assert (
            nc["standardized_url"]
            == "www.oann.com/pm-abe-to-send-message-japan-wont-repeat-war-atrocities-2"
        )
        assert nc["is_generic_url"] is False
        assert nc["response_code"] == 200
        assert nc["response_reason"] == "OK"
        assert nc["fetch_error"] is False
        assert "<!DOCTYPE html>" in nc["resolved_text"]
        assert nc["FETCH_FUNCTION"] == "request_archived_url"
        assert isinstance(
            datetime.datetime.fromisoformat(nc["FETCH_AT"]), datetime.datetime
        )

    def test_nonarchived_url(self, nonarchived_url):
        """Check a URL which is not archived by the Internet Archive's Wayback Machine."""
        url = nonarchived_url
        req = request_archived_url(url)
        nc = json.loads(req)
        assert nc["fetch_error"] is True


class TestFetchUrl(object):
    def test_live_url(self, live_url):
        """Request a URL which is actively served by the domain.
        The NewsContent instance should be from request_active_url and return False for fetch_error.
        This test will fail if 'live_url' doesn't exist anymore.
        """
        url = live_url
        req = fetch_url(url)
        nc = json.loads(req)
        assert (nc["fetch_error"] is False) & (
            nc["FETCH_FUNCTION"] == "request_active_url"
        )

    def test_dead_url(self, dead_url):
        """Check a URL which doesn't exist on the domain anymore.
        The NewsContent instance should be from request_archived_url (fetch_error can be True or False)."""
        url = dead_url
        req = fetch_url(url)
        nc = json.loads(req)
        assert (nc["FETCH_FUNCTION"] == "request_archived_url") & (
            (nc["fetch_error"] is True) | (nc["fetch_error"] is False)
        )


class TestFetchUrls(object):
    def test_one_url(self, live_url):
        """Check one URL with each fetching function"""
        url_dict = {"url": live_url}
        gen_fetched = fetch_urls(urls=url_dict, fetch_function=fetch_url)
        nc_fetched = [json.loads(r) for r in gen_fetched]
        assert len(nc_fetched) == 1

        gen_active = fetch_urls(urls=url_dict, fetch_function=request_active_url)
        nc_active = [json.loads(r) for r in gen_active]
        assert len(nc_active) == 1

        req_archived = fetch_urls(urls=url_dict, fetch_function=request_archived_url)
        nc_archived = [json.loads(r) for r in req_archived]
        assert len(nc_archived) == 1

    def test_many_urls(self, live_url, dead_url):
        "Check a list of URLs with each fetching function"

        url_dicts = [{"url": live_url}, {"url": dead_url}]

        gen_fetched = fetch_urls(urls=url_dicts, fetch_function=fetch_url)
        nc_fetched = [json.loads(r) for r in gen_fetched]
        assert len(nc_fetched) == 2

        gen_active = fetch_urls(
            urls=url_dicts,
            fetch_function=request_active_url,
        )
        nc_active = [json.loads(r) for r in gen_active]
        assert len(nc_active) == 2

        gen_archived = fetch_urls(
            urls=url_dicts,
            fetch_function=request_archived_url,
        )
        nc_archived = [json.loads(r) for r in gen_archived]
        assert len(nc_archived) == 2


class TestFetchUrlsToFile(object):
    def test_one_url(self, live_url, tmpdir):
        """Check one URL with each fetching function"""

        url_dict = {"url": live_url}

        # 1. fetch_url
        p1 = tmpdir
        fn1 = "fetch_url.jsonl"
        fetch_urls_to_file(
            urls=url_dict,
            fetch_function=fetch_url,
            path=p1,
            filename=fn1,
            write_mode="a",
            verbose=1,
        )
        gen_f1 = load_fetched_from_file(path=p1, filename=fn1)
        nc_f1 = [json.loads(r) for r in gen_f1]
        assert len(nc_f1) == 1

        # 2. request_active_url
        p2 = tmpdir
        fn2 = "request_active_url.jsonl"
        fetch_urls_to_file(
            urls=url_dict,
            fetch_function=request_active_url,
            path=p2,
            filename=fn2,
            write_mode="a",
            verbose=1,
        )
        gen_f2 = load_fetched_from_file(path=p2, filename=fn2)
        nc_f2 = [json.loads(r) for r in gen_f2]
        assert len(nc_f2) == 1

        # 3. request_archived_url
        p3 = tmpdir
        fn3 = "request_archived_url.jsonl"
        fetch_urls_to_file(
            urls=url_dict,
            fetch_function=request_archived_url,
            path=p3,
            filename=fn3,
            write_mode="a",
            verbose=1,
        )
        gen_f3 = load_fetched_from_file(path=p3, filename=fn3)
        nc_f3 = [json.loads(r) for r in gen_f3]
        assert len(nc_f3) == 1

    def test_many_urls(self, live_url, dead_url, tmpdir):
        "Check a list of URLs with each fetching function"

        url_dicts = [{"url": live_url}, {"url": dead_url}]

        # 1. fetch_url
        p1 = tmpdir
        fn1 = "fetch_url.jsonl"
        fetch_urls_to_file(
            urls=url_dicts,
            fetch_function=fetch_url,
            path=p1,
            filename=fn1,
            write_mode="a",
            verbose=1,
        )
        gen_f1 = load_fetched_from_file(path=p1, filename=fn1)
        nc_f1 = [json.loads(r) for r in gen_f1]
        assert len(nc_f1) == 2

        # 2. request_active_url
        p2 = tmpdir
        fn2 = "request_active_url.jsonl"
        fetch_urls_to_file(
            urls=url_dicts,
            fetch_function=request_active_url,
            path=p2,
            filename=fn2,
            write_mode="a",
            verbose=1,
        )
        gen_f2 = load_fetched_from_file(path=p2, filename=fn2)
        nc_f2 = [json.loads(r) for r in gen_f2]
        assert len(nc_f2) == 2

        # 3. request_archived_url
        p3 = tmpdir
        fn3 = "request_archived_url.jsonl"
        fetch_urls_to_file(
            urls=url_dicts,
            fetch_function=request_archived_url,
            path=p3,
            filename=fn3,
            write_mode="a",
            verbose=1,
        )
        gen_f3 = load_fetched_from_file(path=p3, filename=fn3)
        nc_f3 = [json.loads(r) for r in gen_f3]
        assert len(nc_f3) == 2
