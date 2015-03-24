__author__ = 'romc'

import unittest
from kb.tools import ojs

class MyTestCase(unittest.TestCase):
    def test_something(self):
        ojs.getJournalPath(1,1)
        self.assertEqual(True, False)


if __name__ == '__main__':
    unittest.main()
