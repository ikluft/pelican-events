"""unit tests for pelican_events plugin for Pelican."""

import unittest

import pelican.plugins.pelican_events

TEST_CASES = {
    "strip_html_tags": (
        {"in": "no HTML here", "out": "no HTML here"},
        {"in": "<i>italic</i>", "out": "_italic_"},
        {"in": "<b>bold</b>", "out": "**bold**"},
    ),
}


class TestCaseSet(unittest.TestCase):
    """Base class for test case sets."""

    @classmethod
    def case_set(cls):
        """Return name of test case set - abstract function to be redefined in subclasses."""
        raise NotImplementedError("define and use case_set() in subclasses")


class TestStripHtmlTags(TestCaseSet):
    """Tests for strip_html_tags()."""

    @classmethod
    def case_set(cls):
        """Return name of test case set."""
        return "strip_html_tags"

    def test_strip_html_tags(self):
        """Subtests for strip_html_tags()."""
        for test_num, test_case in enumerate(TEST_CASES[self.__class__.case_set()]):
            with self.subTest(
                type=self.__class__.case_set(), number=test_num, text=test_case["in"]
            ):
                self.assertEqual(
                    pelican.plugins.pelican_events.strip_html_tags(test_case["in"]),
                    test_case["out"],
                )


if __name__ == "__main__":
    unittest.main()
