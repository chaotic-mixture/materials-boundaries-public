"""Regression guards for the separate installed-wheel smoke checker."""
from email.parser import Parser
import unittest

from scripts.check_wheel_metadata import check_metadata, literal_version


class WheelMetadataTests(unittest.TestCase):
    def metadata(self, *requirements, version="1.2.3", name="materials-boundaries"):
        return Parser().parsestr(f"Name: {name}\nVersion: {version}\n" + "".join(
            f"Requires-Dist: {requirement}\n" for requirement in requirements))

    def test_allows_no_dependencies_and_explicit_dev_extra(self):
        for requirements in [(), ('jsonschema[format-nongpl]<5,>=4.18; extra == "dev"',),
                             ("jsonschema; extra == 'dev'",)]:
            check_metadata(self.metadata(*requirements), "1.2.3")

    def test_rejects_runtime_dependencies_including_conditional_ones(self):
        for requirement in ("unexpected-package==99.0", 'unexpected; python_version < "3.11"',
                            'unexpected; extra == "dev" or python_version >= "3.10"',
                            'unexpected; extra != "dev"', 'unexpected; extra == "other"'):
            with self.subTest(requirement=requirement), self.assertRaisesRegex(RuntimeError, "non-dev dependency"):
                check_metadata(self.metadata(requirement), "1.2.3")

    def test_rejects_wrong_project_or_version(self):
        for metadata in (self.metadata(name="other"), self.metadata(version="0.0.0")):
            with self.assertRaises(RuntimeError):
                check_metadata(metadata, "1.2.3")

    def test_version_is_read_without_execution(self):
        self.assertEqual(literal_version('__version__ = "1.2.3"\nraise RuntimeError("not executed")'), "1.2.3")
        for source in ('__version__ = str(123)', '__version__ = "1"\n__version__ = "2"'):
            with self.assertRaises((ValueError, RuntimeError)):
                literal_version(source)
