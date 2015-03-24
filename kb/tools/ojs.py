__author__ = 'romc'
import urllib.request

def getJournalPath(server, issn):
    """
    :param server: url of the ojs installation, not including protocol
    :param issn: issn of the relevant journal
    :return: string journal path
    :throw error if not found or invalid issn
    """
    url = 'http://' + server + "/issn.php" + "?eissn=%s" % issn
    f = urllib.request.urlopen(url)
    result = f.read().decode('utf-8')
    if 'ERROR' in result:
        raise Exception(result)
    else:
        return result
