import collections

from portal.models import *


def add_highlight_html(text, tag, index):
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


def populate_ann_db(file, data, contents, language, user_id):
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
                           file=file, type=type, language=language,
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
    sense_array = [slist[0]]
    if (len(slist) > 1):
        sense_array.append(slist[0] + "." + slist[1])
    if (len(slist) > 2):
        sense_array.append(slist[0] + "." + slist[1] + "." + slist[2])
    return sense_array


def prepareConnList(connectives):
    conn_array = dict()
    for c in connectives:
        if (c['type'] != 'Explicit') and (c['type'] != 'AltLex'):
            continue
        elif c['conn2'].lower() != 'none':
            conn_array[c['conn'] + " " + c['conn2']] = " (" + c['type'] + ")"
        else:
            conn_array[c['conn']] = " (" + c['type'] + ")"

    sorted_array = collections.OrderedDict(sorted(conn_array.items()))
    return sorted_array
