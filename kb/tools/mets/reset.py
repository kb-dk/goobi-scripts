#!/usr/bin/env python
# -*- coding: utf-8
import os
from datetime import datetime
from xml.etree.ElementTree import ElementTree, ParseError


def reset_mets_file(folder, test=False, debug=False):
    """
    This function resets a METS-file (meta.xml) to it's initial state. This makes it possible to re-run the workflow.
    The following is cleared out:
    * all "dmdSec" with "ID" above "DMDLOG_0001"
      * Corresponding elements in "structMap" with attrib "TYPE" = "LOGICAL" where "DMDID" == "ID" from above
    * all subelemens within "fileSec"
    * all subelemens within "structMap" with attrib "TYPE" == "PHYSICAL"
    * all subelemens within "structLink"
    """
    def delete_sub_elements(_tree, elem_name, attrib_tuple=None):
        if attrib_tuple:
            if debug:
                print('Deleting subelements with name {0} and attributes {1} in tree'.format(elem_name, attrib_tuple))
            k, v = attrib_tuple
            xpath = "./{0}[@{1}='{2}']".format(elem_name, k, v)
            elems = _tree.findall(xpath)
            elem = elems[0] if elems else None
        else:
            if debug:
                print('Deleting elements with name {0} in tree'.format(elem_name))
            elem = _tree.find("./{0}".format(elem_name))
        if not elem:
            # element doesnt exists:
            return
        subelems = elem.findall("./*")
        for subelem in subelems:
            if debug:
                print('\tDeleting {0} with attrib {1} in {2}'.format(subelem.tag, subelem.attrib, elem.tag))
            else:
                elem.remove(subelem)
        return _tree

    input_file = os.path.join(folder, 'meta.xml')
    output_file = input_file
    if test:
        output_file = os.path.join(folder, '{0}_meta_test.xml'.format(datetime.now().strftime("%Y%m%d-%H%M%S")))
    etree = ElementTree()
    try:
        etree.parse(input_file)
        tree = etree.parse(input_file)
    except ParseError as e:
        err_msg = ('resetMetsFile: {0} kunne ikkes parses af ElementTree. '
                   'Procesmappen ignoreres og der fortættes. Fejl besked: {1}')
        print(err_msg.format(input_file, e))
        return False
    """
    * all "dmdSec" with "ID" above "DMDLOG_0001"
        * Corresponding elements in "structMap" with attrib "TYPE" = "LOGICAL" where "DMDID" == "ID" from above.
    """
    mets_ns = '{http://www.loc.gov/METS/}'
    pivot_id = 1
    log_structmap = tree.find("./{0}structMap[@TYPE='LOGICAL']".format(mets_ns))
    dmdsecs = tree.findall(".//{0}dmdSec".format(mets_ns))
    dmdsec_parent = tree.find(".//{0}dmdSec/..".format(mets_ns))
    del_list = []
    if debug:
        print('Deleting dmdSecs and links to these in logical struct map')
    for dmdsec in dmdsecs:
        _id = dmdsec.attrib['ID']
        if 'dmdlog' in _id.lower() and int(_id.split('_')[-1]) > pivot_id:
            # kan ikke slette under iteration:
            del_list.append(dmdsec)
            # delete corresponding elem in structmap
            temp_parent = log_structmap.find(".//*{0}div[@DMDID='{1}']..".format(mets_ns, _id))
            if temp_parent is None:
                continue
            temp_element = temp_parent.findall("./*[@DMDID='{0}']".format(_id))
            if temp_element is None:
                continue
            if debug:
                print('\tDeleting {0} with attrib {1} in {2}'
                      .format(temp_element[0].tag, temp_element[0].attrib, temp_parent.tag))
            else:
                temp_parent.remove(temp_element[0])
    for d in del_list:
        if debug:
            print('\tDeleting {0} with attrib {1} in {2}'.format(d.tag, d.attrib, dmdsec_parent.tag))
        else:
            dmdsec_parent.remove(d)
    # all subelemens within "fileSec"
    delete_sub_elements(tree, '{0}fileSec'.format(mets_ns))
    # all subelemens within "structMap" with attrib "TYPE" == "PHYSICAL"
    _phys_structmap = tree.find("./{0}structMap[@TYPE='PHYSICAL']".format(mets_ns))
    delete_sub_elements(_phys_structmap, mets_ns+'div', ('TYPE', 'BoundBook'))
    # all subelemens within "structLink"
    delete_sub_elements(tree, '{0}structLink'.format(mets_ns))
    if debug:
        print('Writing tree to {0}'.format(output_file))
    else:
        with open(output_file, 'wb') as f:
            etree.write(f, encoding='utf-8')
    return True
