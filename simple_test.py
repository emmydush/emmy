import unittest


class TestExample(unittest.TestCase):
    def test_basic_math(self):
        self.assertEqual(1 + 1, 2)

    def test_string_operations(self):
        self.assertIn("hello", "hello world")


if __name__ == "__main__":
    unittest.main()
