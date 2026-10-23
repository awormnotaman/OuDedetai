import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from requests.exceptions import MissingSchema

import ou_dedetai.network as network

# Get URL object at global level so it only runs once.
URLOBJ = network.UrlProps('http://ip.me')


class TestLatestReleaseUnavailable(unittest.TestCase):
    def setUp(self):
        tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(tempdir.cleanup)
        cache = patch.object(network.constants, 'NETWORK_CACHE_PATH', f"{tempdir.name}/network.json")
        cache.start()
        self.addCleanup(cache.stop)
        self.requests = network.NetworkRequests(force_clean=True)

    def test_offline(self):
        with patch.object(network, '_net_get', return_value=None):
            with self.assertRaises(network.LatestReleaseUnavailable):
                self.requests.app_latest_version('stable')

    def test_only_pre_releases(self):
        # e.g. FaithLife-Community/test-builds, used by the non-stable channel
        releases = [{
            'tag_name': 'main-latest',
            'prerelease': True,
            'updated_at': '2026-10-01T00:00:00Z',
            'assets': [{'browser_download_url': 'https://example.com/oudedetai'}],
        }]
        with patch.object(network, '_net_get', return_value=json.dumps(releases).encode()):
            with self.assertRaises(network.LatestReleaseUnavailable):
                self.requests.app_latest_version('beta')


class TestNetwork(unittest.TestCase):
    def setUp(self):
        self.empty_json_data = '{\n}\n'

    def test_fileprops_get_size(self):
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / 'file.json'
            f.write_text(self.empty_json_data)
            fo = network.FileProps(f)
            self.assertEqual(fo.size, 4)

    def test_fileprops_get_md5(self):
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / 'file.json'
            f.write_text(self.empty_json_data)
            fo = network.FileProps(f)
            self.assertEqual(fo._get_md5(), 'W3aw7vmviiMAZz4FU/YJ+Q==')

    def test_urlprops_get_headers(self):
        self.assertIsNotNone(URLOBJ.headers)

    def test_urlprops_get_headers_none(self):
        test = network.UrlProps('')
        with self.assertRaises(MissingSchema):
            test.headers

    def test_urlprops_get_size(self):
        self.assertIsNotNone(URLOBJ.size)

    def test_urlprops_get_md5(self):
        self.assertIsNone(URLOBJ.md5)