import unittest

from genesis import Genesis


class TestLogin(unittest.TestCase):

    def test_login(self):
        Genesis('admin@genialis.com', 'admin', 'http://gendev:10180')

if __name__ == '__main__':
    unittest.main()
