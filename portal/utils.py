import collections

from portal.models import *
import xml.dom.minidom as minidom
from django.utils.encoding import smart_unicode


def add_highlight_html(text, tag, index):
    if "arg1" in tag:
        tag = "arg1'" + "id='anno"
    to_replace = "<span class= '" + tag + "'>" + text[index[0]:index[1]] + "</span>"
    text = text[:index[0]] + to_replace + text[index[1]:]
    return text


def handle_overlapping(dict):
    if dict['conn'][0] == dict['arg1'][0] and dict['arg1'][1] > dict['conn'][1]:
        dict['overlapping'] = (dict['conn'][0], dict['conn'][1])
        dict['arg1'] = (dict['conn'][1], dict['arg1'][1])
        dict.pop('conn')
    elif dict['conn'][0] == dict['arg2'][0] and dict['arg2'][1] > dict['conn'][1]:
        dict['overlapping'] = (dict['conn'][0], dict['conn'][1])
        dict['arg2'] = (dict['conn'][1], dict['arg2'][1])
        dict.pop('conn')
    elif dict['conn'][0] == dict['arg2'][0] and dict['conn'][1] == dict['conn'][1]:
        dict['overlapping'] = (dict['conn'][0], dict['conn'][1])
        dict.pop('conn')
        dict.pop('arg2')
    elif dict['conn'][1] == dict['arg2'][1] and dict['conn'][0] < dict['arg2'][1]:
        dict['overlapping'] = (dict['conn'][0], dict['conn'][1])
        dict['arg2'] = (dict['arg2'][0], dict['conn'][0])
        dict.pop('conn')
    elif dict['conn'][0] > dict['arg2'][0] and dict['conn'][1] < dict['arg2'][1]:
        dict['overlapping'] = (dict['conn'][0], dict['conn'][1])
        dict['arg2'] = (dict['arg2'][0], dict['conn'][0])
        dict['arg22'] = (dict['conn'][1], dict['arg2'][1])
        dict.pop('conn')


def update_html(text, annotation):
    index_dict = {"conn": (annotation['connBeg'], annotation['connEnd']),
                  "conn2": (annotation['connBeg2'], annotation['connEnd2']),
                  "arg1": (annotation['arg1Beg'], annotation['arg1End']),
                  "arg12": (annotation['arg1Beg2'], annotation['arg1End2']),
                  "arg2": (annotation['arg2Beg'], annotation['arg2End']),
                  "arg22": (annotation['arg2Beg2'], annotation['arg2End2'])}

    handle_overlapping(index_dict)
    span_beg_dict = {}

    for key in index_dict.keys():
        span_beg_dict[key] = index_dict[key][0]

    ''' 
    keys = span_beg_dict.keys()
    beg_values = span_beg_dict.values()
    end_values = span_end_dict.values()

    indexes = []
    for key, value in index_dict:
        indexes.append(value[0])
        indexes.append(value[1])

    r_sorted_indexes = sorted(indexes, reverse=True)
    prev = r_sorted_indexes[0]
    curr = 0

    for i in range(1, len(r_sorted_indexes)):
        curr = r_sorted_indexes[i]

        if prev != curr
'''

    span_dict_value = span_beg_dict.values()
    span_dict_key = span_beg_dict.keys()
    sorted_span_dic_values = sorted(span_dict_value, reverse=True)

    for s in sorted_span_dic_values:
        if s > 0:
            key = span_dict_key[span_dict_value.index(s)]
            text = add_highlight_html(text, key, index_dict[key])

    return text  # PDTB Annotation Methods


def populate_ann_db(file, data, contents, annotation_tool, user_id):
    contents = contents.replace("\n", "")
    ann_array = data.split("\n")
    for ann in ann_array:
        if len(ann) > 0 and "Rejected" not in ann:
            ann_fields = ann.split("|")
            type = ann_fields[0]

            if ann_fields[1] != "":
                con_index = handle_arg_indices(ann_fields[1])
                conn = recover_arg(con_index, contents)
            elif type == "Implicit":
                con_index = [-1, -1, -1, -1]
                conn = [ann_fields[7], "none"]
            else:
                con_index = [-1, -1, -1, -1]
                conn = ["", "none"]
            arg1_index = handle_arg_indices(ann_fields[14])
            arg1 = recover_arg(arg1_index, contents)
            arg2_index = handle_arg_indices(ann_fields[20])
            arg2 = recover_arg(arg2_index, contents)
            sense1 = ann_fields[8]
            sense2 = ann_fields[9]
            pdtbAnnotation(conn=conn[0], connBeg=con_index[0], connEnd=con_index[1],
                           conn2=conn[1], connBeg2=con_index[2], connEnd2=con_index[3],
                           arg1=arg1[0], arg1Beg=arg1_index[0], arg1End=arg1_index[1],
                           arg12=arg1[1], arg1Beg2=arg1_index[2], arg1End2=arg1_index[3],
                           arg2=arg2[0], arg2Beg=arg2_index[0], arg2End=arg2_index[1],
                           arg22=arg2[1], arg2Beg2=arg2_index[2], arg2End2=arg2_index[3],
                           sense1=sense1, sense2=sense2,
                           file=file, type=type, annotation_tool=annotation_tool,
                           user_id=user_id
                           ).save()


def populate_ann_db_xml(file_name, xml_file, annotation_tool, user_id):
    doc = minidom.parse(xml_file)
    relations = doc.getElementsByTagName("Relation")

    for relation in relations:
        type = relation.getAttribute("type")
        sense = relation.getAttribute("sense")
        sense2 = relation.getAttribute("sense2") if relation.hasAttribute("sense2") else ""

        sense = sense.replace(': ', '.')
        sense2 = sense2.replace(': ', '.')

        conn = ['none', 'none']
        connBeg = [-1, -1]
        connEnd = [-1, -1]
        connectives = relation.getElementsByTagName("Conn")[0].getElementsByTagName("Span")
        for i in range(len(connectives)):
            conn[i] = smart_unicode(connectives[i].getElementsByTagName("Text")[0].firstChild.data)
            connBeg[i] = connectives[i].getElementsByTagName("BeginOffset")[0].firstChild.data
            connEnd[i] = connectives[i].getElementsByTagName("EndOffset")[0].firstChild.data

        arg1 = ['none', 'none']
        arg1Beg = [-1, -1]
        arg1End = [-1, -1]
        argument1 = relation.getElementsByTagName("Arg1")[0].getElementsByTagName("Span")
        for i in range(len(argument1)):
            a = smart_unicode(argument1[i].getElementsByTagName("Text")[0].firstChild.data)
            arg1[i] = a.replace("\n                    ", " ")
            arg1Beg[i] = argument1[i].getElementsByTagName("BeginOffset")[0].firstChild.data
            arg1End[i] = argument1[i].getElementsByTagName("EndOffset")[0].firstChild.data

        arg2 = ['none', 'none']
        arg2Beg = [-1, -1]
        arg2End = [-1, -1]
        argument2 = relation.getElementsByTagName("Arg2")[0].getElementsByTagName("Span")
        for i in range(len(argument2)):
            a = smart_unicode(argument2[i].getElementsByTagName("Text")[0].firstChild.data)
            arg2[i] = a.replace("\n                    ", " ")
            arg2Beg[i] = argument2[i].getElementsByTagName("BeginOffset")[0].firstChild.data
            arg2End[i] = argument2[i].getElementsByTagName("EndOffset")[0].firstChild.data

        pdtbAnnotation(conn=conn[0], connBeg=connBeg[0], connEnd=connEnd[0],
                       conn2=conn[1], connBeg2=connBeg[1], connEnd2=connEnd[1],
                       arg1=arg1[0], arg1Beg=arg1Beg[0], arg1End=arg1End[0],
                       arg12=arg1[1], arg1Beg2=arg1Beg[1], arg1End2=arg1End[1],
                       arg2=arg2[0], arg2Beg=arg2Beg[0], arg2End=arg2End[0],
                       arg22=arg2[1], arg2Beg2=arg2Beg[1], arg2End2=arg2End[1],
                       sense1=sense, sense2=sense2,
                       file=file_name, type=type, annotation_tool=annotation_tool,
                       user_id=user_id
                       ).save()


def recover_arg(index, contents):
    res = [contents[index[0]:index[1]]]
    if index[3] != -1:
        res.append(contents[index[2]:index[3]])
    else:
        res.append("none")
    return res


def handle_arg_indices(arg):
    arg_index_array = []
    if arg.find(";") == -1:
        arg_index_array.append(int(arg.split("..")[0]))
        arg_index_array.append(int(arg.split("..")[1]))
        arg_index_array.append(-1)
        arg_index_array.append(-1)
    else:
        discont_arg = arg.split(";")
        arg_index_array.append(int(discont_arg[0].split("..")[0]))
        arg_index_array.append(int(discont_arg[0].split("..")[1]))
        arg_index_array.append(int(discont_arg[1].split("..")[0]))
        arg_index_array.append(int(discont_arg[1].split("..")[1]))
    return arg_index_array


# PDTB Annotation Methods

def prepareSenseList(senses):
    # sense_array = ['EXPANSION','COMPARISON','CONTINGENCY','TEMPORAL']
    sense_array = []
    for s in senses:
        s1list = s['sense1'].split(".")
        s2list = s['sense2'].split(".")
        sense_array.extend(getSensesAllLevel(s1list))
        sense_array.extend(getSensesAllLevel(s2list))
    sense_array = set(sense_array)
    sense_array = list(sense_array)
    sense_array.sort()
    return sense_array


def getSensesAllLevel(slist):
    sense_array = [slist[0].lower()]
    if (len(slist) > 1):
        sense_array.append(slist[0].lower() + "." + slist[1].lower())
    if (len(slist) > 2):
        sense_array.append(slist[0].lower() + "." + slist[1].lower() + "." + slist[2].lower())
    return sense_array


def prepareConnList(connectives):
    conn_array = dict()
    for c in connectives:
        if (c['type'].lower() != 'Explicit'.lower()) and (c['type'].lower() != 'AltLex'.lower()):
            continue
        elif c['conn2'].lower() != 'none':
            conn_array[c['conn'] + " " + c['conn2']] = " (" + c['type'] + ")"
        else:
            conn_array[c['conn']] = " (" + c['type'] + ")"

    sorted_array = collections.OrderedDict(sorted(conn_array.items()))
    return sorted_array
