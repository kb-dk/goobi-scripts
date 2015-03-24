__author__ = 'romc'

import unittest
from kb.tools import ojs

class testJournalPath(unittest.TestCase):
    """
    Note that this test presumes a local tidsskrift.dk installation
    running on localhost
    """
    def test(self):
        path = ojs.getJournalPath('localhost','1904-4348')
        self.assertEqual(path, 'magasin')


if __name__ == '__main__':
    unittest.main()
