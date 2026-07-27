import unittest
from app.utils.version import compare_versions, is_newer_version

class TestVersionComparison(unittest.TestCase):
    def test_compare_versions_equal(self):
        self.assertEqual(compare_versions("1.0.0", "1.0.0"), 0)
        self.assertEqual(compare_versions("2.1.3", "2.1.3"), 0)

    def test_compare_versions_newer(self):
        self.assertEqual(compare_versions("2.0.0", "1.0.0"), 1)
        self.assertEqual(compare_versions("1.1.0", "1.0.0"), 1)
        self.assertEqual(compare_versions("1.0.1", "1.0.0"), 1)
        self.assertEqual(compare_versions("3.0.0", "2.9.9"), 1)

    def test_compare_versions_older(self):
        self.assertEqual(compare_versions("1.0.0", "2.0.0"), -1)
        self.assertEqual(compare_versions("1.0.0", "1.1.0"), -1)
        self.assertEqual(compare_versions("1.0.0", "1.0.1"), -1)

    def test_compare_versions_different_lengths(self):
        self.assertEqual(compare_versions("1.0", "1.0.0"), 0)
        self.assertEqual(compare_versions("1.0.0", "1.0"), 0)
        self.assertEqual(compare_versions("1.1", "1.0.0"), 1)
        self.assertEqual(compare_versions("1.0", "1.1.0"), -1)

    def test_is_newer_version_true(self):
        self.assertTrue(is_newer_version("2.0.0", "1.0.0"))
        self.assertTrue(is_newer_version("1.1.0", "1.0.0"))
        self.assertTrue(is_newer_version("1.0.1", "1.0.0"))

    def test_is_newer_version_false(self):
        self.assertFalse(is_newer_version("1.0.0", "2.0.0"))
        self.assertFalse(is_newer_version("1.0.0", "1.0.0"))
        self.assertFalse(is_newer_version("1.0.0", "1.1.0"))

if __name__ == '__main__':
    unittest.main()