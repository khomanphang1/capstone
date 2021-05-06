import unittest
from mason import transfer_function


class MyTestCase(unittest.TestCase):
    def test_something(self):
        self.assertEqual(True, False)

        import sympy as sp

        expected_transfer = '(s + 3x - 2) / 23'




if __name__ == '__main__':
    unittest.main()
