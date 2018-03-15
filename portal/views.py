# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import codecs
import csv
import operator
from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseRedirect

from portal.forms import *
from utils import *
from django.db.models import Q

from django.utils.crypto import get_random_string
import json
from django.utils.encoding import smart_unicode
import re


def upload_annotations(request):
    request.session.set_expiry(0)
    if 'user_id' not in request.session:
        user_id = get_random_string(length=32)
        request.session['user_id'] = user_id
    if request.method == 'POST':
        form = DocumentForm(request.POST, request.FILES)
        if form.is_valid():
            ann_tool = request.POST['annotation_tool']
            if ann_tool == 'pdtb':
                data = request.FILES['ann_file'].read()
                contents = smart_unicode(request.FILES['raw_file'].read())
                # language = request.POST['language']
                file_name = request.FILES['ann_file'].name
                pdtbAnnotation.objects.filter(file=file_name).delete()  # if same file is updated again
                populate_ann_db(file_name, data, contents, ann_tool, request.session['user_id'])
                file_object = form.save(commit=False)
                file_object.filename = file_name
                file_object.user_id = request.session['user_id']
                uploaded_files.objects.filter(filename=file_name).delete()  # if same file is updated again
                file_object.save()
            elif ann_tool == 'datt':
                xml_file = request.FILES['ann_file']
                # language = request.POST['language']
                file_name = request.FILES['ann_file'].name
                populate_ann_db_xml(file_name, xml_file, ann_tool, request.session['user_id'])
                file_object = form.save(commit=False)
                file_object.filename = request.FILES['ann_file'].name
                file_object.user_id = request.session['user_id']
                file_object.save()
        return redirect('search_page.html')
    else:
        form = DocumentForm()
    return render(request, 'upload_annotations.html', {
        'form': form
    })


def highlight_rest(request):
    if request.method == 'GET' and 'annotation' in request.GET:
        annotation = pdtbAnnotation.objects.filter(id=request.GET['annotation']).values('connBeg', 'connEnd',
                                                                                        'connBeg2', 'connEnd2',
                                                                                        'arg1Beg', 'arg1End',
                                                                                        'arg1Beg2', 'arg1End2',
                                                                                        'arg2Beg', 'arg2End',
                                                                                        'arg2Beg2', 'arg2End2',
                                                                                        'file')[0]

        ann_tool = pdtbAnnotation.objects.filter(id=request.GET['annotation']).values('annotation_tool')[0]

        if ann_tool['annotation_tool'] == 'datt':
            with codecs.open(uploaded_files.objects.filter(filename=annotation['file'])[0].raw_file.path, 'r',
                             encoding='utf8') as f:
                text = f.read().replace("\n", " ")
        else:
            with codecs.open(uploaded_files.objects.filter(filename=annotation['file'])[0].raw_file.path, 'r',
                             encoding='utf8') as f:
                text = f.read().replace("\n", "")

    if request.method == 'GET' and 'ted_mdb_annotation' in request.GET:
        annotation = \
            ted_mdb_annotation.objects.filter(ann_id=request.GET['ted_mdb_annotation'],
                                              file__contains=request.GET['file']).values('connBeg', 'connEnd',
                                                                                         'connBeg2', 'connEnd2',
                                                                                         'arg1Beg', 'arg1End',
                                                                                         'arg1Beg2', 'arg1End2',
                                                                                         'arg2Beg', 'arg2End',
                                                                                         'arg2Beg2', 'arg2End2',
                                                                                         'file')[0]
        text = ted_mdb_files.objects.filter(filename=annotation['file'])[0].raw_file

    text = update_html(text, annotation)
    return HttpResponse(text)


####### TED - MDB  #######

def ted_mdb(request):
    if request.method == 'GET' and 'language' in request.GET and "sec_lang" not in request.GET:
        selected_language = request.GET['language']
        documents = ted_mdb_files.objects.values('filename').filter(language=selected_language)
        result_files = dict()
        for d in documents:
            result_files[d['filename']] = d['filename']
        return HttpResponse(json.dumps(result_files))

    if request.method == 'GET' and 'file' in request.GET:
        selected_file_name = request.GET['file']
        selected_file = ted_mdb_files.objects.filter(filename=selected_file_name).first()
        content = selected_file.raw_file
        annotations = ted_mdb_annotation.objects.filter(file=selected_file_name).order_by('arg1Beg')
        annotation_list = dict()

        for a in annotations:
            annotation_list[a.ann_id] = a.conn + " (" + a.type + ") |" + a.sense1 + "|" + a.sense2
        annotation_list = collections.OrderedDict(sorted(annotation_list.items()))
        connectives = ted_mdb_annotation.objects.filter(file=selected_file_name).values('conn', 'conn2',
                                                                                        'type').order_by(
            'conn').distinct()
        connective_array = prepareConnList(connectives)

        result = dict()
        result['annotation_list'] = annotation_list
        result['connective_list'] = connective_array
        result['text'] = content

        if '2150' in request.GET['file']:
            selected_eng_file_name = "talk_2150_en.txt"
        else:
            selected_eng_file_name = "talk_2009_en.txt"
        selected_eng_file = ted_mdb_files.objects.filter(filename=selected_eng_file_name).first()
        eng_content = selected_eng_file.raw_file
        eng_annotations = ted_mdb_annotation.objects.filter(file=selected_eng_file_name)
        eng_annotation_list = dict()
        for a in eng_annotations:
            eng_annotation_list[a.ann_id] = a.conn + " (" + a.type + ") |" + a.sense1 + "|" + a.sense2

        result['eng_annotation_list'] = eng_annotation_list
        result['eng_text'] = eng_content
        return HttpResponse(json.dumps(result))

    # ON LOAD
    all_languages = ted_mdb_files.objects.values('language').filter(~Q(language="English")).distinct()
    first_doc = ted_mdb_files.objects.filter(language=all_languages.first()['language']).first()
    selected_language = first_doc.language

    if request.method == 'GET' and 'language' in request.GET:
        selected_language = request.GET['language']
        first_doc = ted_mdb_files.objects.filter(language=selected_language).first()

    selected_file_name = first_doc.filename
    selected_file_content = first_doc.raw_file
    documents = ted_mdb_files.objects.filter(language=selected_language)

    annotations = ted_mdb_annotation.objects.filter(file=selected_file_name).order_by('arg1Beg')
    senses = ted_mdb_annotation.objects.filter(file=selected_file_name).values('sense1', 'sense2').distinct()
    connectives = ted_mdb_annotation.objects.filter(file=selected_file_name).values('conn', 'conn2', 'type').distinct()
    connective_array = prepareConnList(connectives)

    sense_array = prepareSenseList(senses)

    if '2150' in selected_file_name:
        selected_eng_file_name = "talk_2150_en.txt"
    else:
        selected_eng_file_name = "talk_2009_en.txt"

    eng_annotations = ted_mdb_annotation.objects.filter(file=selected_eng_file_name)
    eng_text = ted_mdb_files.objects.filter(filename=selected_eng_file_name).first().raw_file

    return render(request, 'ted_mdb.html', {'all_languages': all_languages,
                                            'documents': documents,
                                            'annotations': annotations,
                                            'selected_file_content': selected_file_content,
                                            'selectedFileName': selected_file_name,
                                            'senses': sense_array,
                                            'connective_array': connective_array,
                                            'eng_annotations': eng_annotations,
                                            'eng_text': eng_text
                                            })


def ted_mdb_rest(request):
    selected_file_name = request.GET['file']
    selected_file = ted_mdb_files.objects.filter(filename=selected_file_name).first()
    content = selected_file.raw_file
    annotation_list = dict()
    annotation_list["text"] = content  # change return object
    annotations = ted_mdb_annotation.objects.filter(file=selected_file_name).order_by("arg1Beg")
    english_annotation_set = dict()

    if '2150' in request.GET['file']:
        selected_eng_file_name = "talk_2150_en.txt"
    else:
        selected_eng_file_name = "talk_2009_en.txt"

    # SENSE1, !SENSE2
    if request.method == 'GET' and 'file' in request.GET and 'sense' in request.GET and 'sense2' not in request.GET:
        selected_senses = request.GET['sense'].replace(" ", "")
        selected_senses = selected_senses.split(',')
        annotations = annotations.filter(
            reduce(operator.or_, (Q(sense1__icontains=s) | Q(sense2__icontains=s) for s in selected_senses)))
    # SENSE1, SENSE2
    if request.method == 'GET' and 'file' in request.GET and 'sense' in request.GET and 'sense2' in request.GET:
        selected_senses = request.GET['sense'].replace(" ", "")
        selected_senses2 = request.GET['sense2'].replace(" ", "")
        query_operator = request.GET['op']
        selected_senses = selected_senses.split(',')
        selected_senses2 = selected_senses2.split(',')
        annotations = annotations.filter(
            reduce(operator.or_, (Q(sense1__icontains=s) for s in selected_senses)),
            reduce(operator.or_, (Q(sense2__icontains=s2) for s2 in selected_senses2)))
    # CONN
    if request.method == 'GET' and 'file' in request.GET and "connective" in request.GET:
        selected_connectives = request.GET['connective']
        selected_connectives = selected_connectives.split(',')
        annotations = annotations.filter(
            reduce(operator.or_, (Q(conn=c) for c in selected_connectives)))
    # TYPE
    if request.method == 'GET' and 'file' in request.GET and "type" in request.GET:
        selected_types = request.GET['type']
        selected_types = selected_types.split(',')
        annotations = annotations.filter(
            reduce(operator.or_, (Q(type=t) for t in selected_types)))

    if 'targetSense'  in request.GET and 'targetType' in request.GET:
        selected_target_types = request.GET['targetType'].split(',');
        selected_target_senses = request.GET['targetSense'].split(',');
        eng_equivalent_ids = ted_mdb_alignment.objects.filter(
            reduce(operator.or_, (Q(sl_id=a.ann_id) for a in annotations)), sl_file=request.GET['file'])
        eng_annotation = ted_mdb_annotation.objects.filter(
            reduce(operator.or_, (Q(ann_id=a.fl_id) for a in eng_equivalent_ids)),
            reduce(operator.or_, (Q(sense1__icontains=s) | Q(sense2__icontains=s) for s in selected_target_senses)),
            reduce(operator.or_, (Q(type=t) for t in selected_target_types)),
            file=selected_eng_file_name)
        if (len(eng_annotation) > 0):
            source_equivalent_ids = ted_mdb_alignment.objects.filter(
                reduce(operator.or_, (Q(fl_id=a.ann_id) for a in eng_annotation)), sl_file=request.GET['file'])
            annotations = ted_mdb_annotation.objects.filter(
                reduce(operator.or_, (Q(ann_id=a.sl_id) for a in source_equivalent_ids)),
                file=selected_file_name)
            for a in eng_annotation:
                english_annotation_set[a.ann_id] = a.conn + " (" + a.type + ")" + " | " + a.sense1 + " | " + a.sense2

    elif request.method == 'GET' and 'targetType' in request.GET:
        selected_target_types = request.GET['targetType'].split(',');
        eng_equivalent_ids = ted_mdb_alignment.objects.filter(
            reduce(operator.or_, (Q(sl_id=a.ann_id) for a in annotations)), sl_file=request.GET['file'])
        eng_annotation = ted_mdb_annotation.objects.filter(
            reduce(operator.or_, (Q(ann_id=a.fl_id) for a in eng_equivalent_ids)),
            reduce(operator.or_, (Q(type=t) for t in selected_target_types)),
            file=selected_eng_file_name)
        if (len(eng_annotation) > 0):
            source_equivalent_ids = ted_mdb_alignment.objects.filter(
                reduce(operator.or_, (Q(fl_id=a.ann_id) for a in eng_annotation)), sl_file=request.GET['file'])
            annotations = ted_mdb_annotation.objects.filter(
                reduce(operator.or_, (Q(ann_id=a.sl_id) for a in source_equivalent_ids)),
                file=selected_file_name)
            for a in eng_annotation:
                english_annotation_set[a.ann_id] = a.conn + " (" + a.type + ")" + " | " + a.sense1 + " | " + a.sense2

    elif request.method == 'GET' and 'targetSense' in request.GET:
        selected_target_senses = request.GET['targetSense'].split(',');
        eng_equivalent_ids = ted_mdb_alignment.objects.filter(
            reduce(operator.or_, (Q(sl_id=a.ann_id) for a in annotations)), sl_file=request.GET['file'])
        eng_annotation = ted_mdb_annotation.objects.filter(
            reduce(operator.or_, (Q(ann_id=a.fl_id) for a in eng_equivalent_ids)),
            reduce(operator.or_, (Q(sense1__icontains=s) | Q(sense2__icontains=s) for s in selected_target_senses)),
            file=selected_eng_file_name)
        if (len(eng_annotation) > 0):
            source_equivalent_ids = ted_mdb_alignment.objects.filter(
                reduce(operator.or_, (Q(fl_id=a.ann_id) for a in eng_annotation)), sl_file=request.GET['file'])
            annotations = ted_mdb_annotation.objects.filter(
                reduce(operator.or_, (Q(ann_id=a.sl_id) for a in source_equivalent_ids)),
                file=selected_file_name)
            for a in eng_annotation:
                english_annotation_set[a.ann_id] = a.conn + " (" + a.type + ")" + " | " + a.sense1 + " | " + a.sense2

    if 'targetSense' not in request.GET and 'targetType' not in request.GET:
        eng_equivalent_ids = ted_mdb_alignment.objects.filter(
            reduce(operator.or_, (Q(sl_id=a.ann_id) for a in annotations)), sl_file=request.GET['file'])
        if (len(eng_equivalent_ids) > 0):
            eng_annotation = ted_mdb_annotation.objects.filter(
                reduce(operator.or_, (Q(ann_id=a.fl_id) for a in eng_equivalent_ids)),
                file=selected_eng_file_name)
            for a in eng_annotation:
                english_annotation_set[a.ann_id] = a.conn + " (" + a.type + ")" + " | " + a.sense1 + " | " + a.sense2

    for a in annotations:
        annotation_list[a.ann_id] = a.conn + " (" + a.type + ")" + " | " + a.sense1 + " | " + a.sense2
    result = dict()
    result['text'] = content
    result['annotation_list'] = annotation_list
    result['eng_annotation_list'] = english_annotation_set

    return HttpResponse(json.dumps(result))


####### ALIGNMENT  #######

def ted_mdb_get_aligned(request):
    if request.method == 'GET' and 'annotation' in request.GET and 'file' in request.GET:
        annotation_id = request.GET['annotation']
        file_name = request.GET['file']
        try:
            eng_eq = ted_mdb_alignment.objects.filter(sl_id=annotation_id, sl_file=file_name)
            if '2150' in file_name:
                selected_eng_file_name = "talk_2150_en.txt"
            else:
                selected_eng_file_name = "talk_2009_en.txt"
            eng_annotation_list = ted_mdb_annotation.objects.filter(
                reduce(operator.or_, (Q(ann_id=id.fl_id) for id in eng_eq)),
                file=selected_eng_file_name)
            result = dict()

            for eng_annotation in eng_annotation_list:
                result[eng_annotation.ann_id] = eng_annotation.conn + " (" + eng_annotation.type + ")" \
                                                + " | " + eng_annotation.sense1 + " | " + eng_annotation.sense2

            return HttpResponse(json.dumps(result))
        except:
            pass


####### TED - MDB  #######


####### SEARCH ##############


def search_sense_rest(request):
    if request.method == 'POST':
        return redirect('upload_annotations.html')

    file_array = uploaded_files.objects.all()
    all_results = {}

    annotations_dict = {}

    for file in file_array:
        selected_file_name = file.filename
        content = file.raw_file.read()
        annotation_list = []
        annotations = pdtbAnnotation.objects.filter(file=selected_file_name).order_by('arg1Beg')
        # SENSE1, !SENSE2
        if request.method == 'GET' and 'file' in request.GET and 'sense' in request.GET and 'sense2' not in request.GET:
            selected_senses = request.GET['sense'].replace(" ", "")
            selected_senses = selected_senses.split(',')
            annotations = annotations.filter(
                reduce(operator.or_, (Q(sense1__icontains=s) | Q(sense2__icontains=s) for s in selected_senses)))
        # SENSE1, SENSE2
        if request.method == 'GET' and 'file' in request.GET and 'sense' in request.GET and 'sense2' in request.GET:
            selected_senses = request.GET['sense'].replace(" ", "")
            selected_senses2 = request.GET['sense2'].replace(" ", "")
            query_operator = request.GET['op']
            selected_senses = selected_senses.split(',')
            selected_senses2 = selected_senses2.split(',')
            if query_operator == "and":
                tmp1 = annotations.filter(
                    reduce(operator.or_, (Q(sense1__icontains=s) for s in selected_senses)),
                    reduce(operator.or_, (Q(sense2__icontains=s2) for s2 in selected_senses2)))
                tmp2 = annotations.filter(
                    reduce(operator.or_, (Q(sense2__icontains=s) for s in selected_senses)),
                    reduce(operator.or_, (Q(sense1__icontains=s2) for s2 in selected_senses2)))
                annotations = tmp1 | tmp2
            else:
                tmp1 = annotations.filter(
                    reduce(operator.or_, (Q(sense1__icontains=s) for s in selected_senses)))
                tmp1 = tmp1.exclude(
                    reduce(operator.or_, (Q(sense2__icontains=s2) for s2 in selected_senses2)))
                tmp1 = tmp1.exclude(Q(sense2=""))


                tmp2 = annotations.filter(
                    reduce(operator.or_, (Q(sense2__icontains=s) for s in selected_senses)))
                tmp2 = tmp2.exclude(
                    reduce(operator.or_, (Q(sense1__icontains=s2) for s2 in selected_senses2)))
                tmp2 = tmp2.exclude(Q(sense2=""))
                annotations = tmp1 | tmp2

        # CONN
        if request.method == 'GET' and 'file' in request.GET and "connective" in request.GET:
            selected_connectives = request.GET['connective'].replace(" ", "")
            selected_connectives = selected_connectives.split(',')
            annotations = annotations.filter(
                reduce(operator.or_, (Q(conn=c) for c in selected_connectives)))
        # TYPE
        if request.method == 'GET' and 'file' in request.GET and "type" in request.GET:
            selected_types = request.GET['type']
            selected_types = selected_types.split(',')
            annotations = annotations.filter(
                reduce(operator.or_, (Q(type=t) for t in selected_types)))

        if request.method == 'GET' and 'file' in request.GET and "keyword-arg1" in request.GET:
            keyword = request.GET['keyword-arg1']
            keyword_list = prepareKeyword(keyword)
            annotations = annotations.filter(
                reduce(operator.or_, (Q(arg1__contains=k) for k in keyword_list)))

        if request.method == 'GET' and 'file' in request.GET and "keyword-arg2" in request.GET:
            keyword = request.GET['keyword-arg2']
            keyword_list = prepareKeyword(keyword)
            annotations = annotations.filter(
                reduce(operator.or_, (Q(arg2__contains=k) for k in keyword_list)))

        for a in annotations:
            annotation_list.append(a.conn + " (" + a.type + ")" + " | " + a.sense1 + " | " + a.sense2 + "#" + str(a.id))
        result = dict()
        result['text'] = content
        result['annotation_list'] = annotation_list

        annotations_dict[selected_file_name] = annotations
        all_results[file.id] = result

    request.session['search_results'] = annotations_dict

    return HttpResponse(json.dumps(all_results))


# ONLOAD
def search_page_rest(request):
    documents = uploaded_files.objects.filter()

    if request.method == 'GET' and 'reset' in request.GET:
        file_array = uploaded_files.objects.all()

        all_results = dict()
        annotations_array = {}
        annotations_dict = {}
        file_ids = []

        for file in file_array:
            annotation_list = []
            selected_file_name = file.filename
            file_ids.append(file.id)
            annotations_array[file.id] = pdtbAnnotation.objects.filter(file=selected_file_name).order_by('arg1Beg')
            annotations_dict[selected_file_name] = annotations_array[file.id]
            result = dict()
            result['text'] = file.raw_file.read()
            for a in annotations_array[file.id]:
                annotation_list.append(
                    a.conn + " (" + a.type + ")" + " | " + a.sense1 + " | " + a.sense2 + "#" + str(a.id))
            result['annotation_list'] = annotation_list
            all_results[file.id] = result

        request.session['search_results'] = annotations_dict
        return HttpResponse(json.dumps(all_results))

    if request.method == 'POST':
        return redirect('upload_annotations.html')

    # ON LOAD

    file_array = uploaded_files.objects.all()

    if (file_array.count() == 0):
        return redirect('upload_annotations.html')

    annotations_array = {}
    annotations_dict = {}
    file_ids = []

    all_senses = list()
    all_connectives = {}

    keyword_arg1 = []
    keyword_arg2 = []

    for file in file_array:
        selected_file_name = file.filename
        file_ids.append(file.id)
        annotations_array[file.id] = pdtbAnnotation.objects.filter(file=selected_file_name).order_by('arg1Beg')
        annotations_dict[selected_file_name] = annotations_array[file.id]
        senses = pdtbAnnotation.objects.filter(file=selected_file_name).values('sense1',
                                                                               'sense2').distinct()
        sense_array = prepareSenseList(senses)
        all_senses.extend(sense_array)

        connectives = pdtbAnnotation.objects.filter(file=selected_file_name).values(
            'conn', 'conn2',
            'type').distinct()
        connective_array = prepareConnList(connectives)
        all_connectives.update(connective_array)

        arg1 = pdtbAnnotation.objects.filter(file=selected_file_name).values('arg1',
                                                                             'arg12').distinct()
        for arg in arg1:
            if arg['arg1'] != 'none': keyword_arg1.extend(re.split(r'[:;,#\"\'?.\s]\s*', arg['arg1']))
            if arg['arg12'] != 'none': keyword_arg1.extend(re.split(r'[:;,#\"\'?.\s]\s*', arg['arg12']))

        arg2 = pdtbAnnotation.objects.filter(file=selected_file_name).values('arg2',
                                                                             'arg22').distinct()
        for arg in arg2:
            if arg['arg2'] != 'none': keyword_arg2.extend(re.split(r'[:;,#\"\'?.\s]\s*', arg['arg2']))
            if arg['arg22'] != 'none': keyword_arg2.extend(re.split(r'[:;,#\"\'?.\s]\s*', arg['arg22']))

    all_senses = set(all_senses)
    all_senses = list(all_senses)
    all_senses.sort()

    keyword_arg1 = set(keyword_arg1)
    keyword_arg1 = list(keyword_arg1)
    keyword_arg1.sort()

    keyword_arg2 = set(keyword_arg2)
    keyword_arg2 = list(keyword_arg2)
    keyword_arg2.sort()

    all_connectives = collections.OrderedDict(all_connectives)

    request.session['search_results'] = annotations_dict

    first = uploaded_files.objects.filter().first()
    selected_file_name = first.filename
    selected_file = uploaded_files.objects.filter(filename=selected_file_name).first()
    annotations = pdtbAnnotation.objects.filter(file=selected_file_name)

    return render(request, 'search_page.html', {'documents': documents, 'annotations': annotations,
                                                'selectedFile': selected_file,
                                                'selectedFileName': selected_file_name,
                                                'senses': all_senses,
                                                'connective_array': all_connectives,
                                                'file_array': file_array,
                                                'annotations_array': annotations_array,
                                                'file_ids': file_ids,
                                                'keyword_arg1': keyword_arg1,
                                                'keyword_arg2': keyword_arg2
                                                })


####### SEARCH ##############

def compute_total_stats(request):
    senses = ['TEMPORAL', 'CONTINGENCY', 'COMPARISON', 'EXPANSION']
    types = ['Explicit', 'Implicit', 'AltLex', 'EntRel', 'NoRel']
    stats = {}
    if request.method == 'GET' and 'type' in request.GET and 'sense' in request.GET and 'base' in request.GET:
        dis_type = request.GET['type']
        sense = request.GET['sense']
        base = request.GET['base']

    if base == 'dis-type':
        stats['title'] = 'Sense Distribution According to'
        stats['coloums'] = []
        stats['coloums'].append(['Senses', 'Counts'])
        if dis_type == 'ALL':
            for s in senses:
                s_count = pdtbAnnotation.objects.filter(
                    Q(sense1__icontains=s) | Q(sense2__icontains=s)).count()

                stats['coloums'].append([s, s_count])

            stats['title'] = stats['title'] + ' ALL Discourse Types'
        else:
            type_ann = pdtbAnnotation.objects.filter(
                type=dis_type)
            for s in senses:
                s_count = type_ann.filter(
                    Q(sense1__icontains=s) | Q(sense2__icontains=s)).count()

                stats['coloums'].append([s, s_count])

            stats['title'] = stats['title'] + ' ' + dis_type + ' Discourse Type'

    elif base == 'sense':
        stats['title'] = 'Discourse Type Distribution in '
        stats['coloums'] = []
        stats['coloums'].append(['Discourse Types', 'Counts'])
        if sense == 'ALL':
            for t in types:
                t_count = pdtbAnnotation.objects.filter(type=t).count()
                stats['coloums'].append([t, t_count])

            stats['title'] = stats['title'] + ' ALL Relations'
        else:
            sense_ann = pdtbAnnotation.objects.filter(Q(sense1__icontains=sense) | Q(sense2__icontains=sense))
            for t in types:
                t_count = sense_ann.filter(type=t).count()
                stats['coloums'].append([t, t_count])

            stats['title'] = stats['title'] + ' Relations with ' + sense + ' Sense'

    return HttpResponse(json.dumps(stats))


def compute_files_stats(request):
    senses = ['TEMPORAL', 'CONTINGENCY', 'COMPARISON', 'EXPANSION']
    types = ['Explicit', 'Implicit', 'AltLex', 'EntRel', 'NoRel']

    if request.method == 'GET' and 'type' in request.GET and 'sense' in request.GET and 'base' in request.GET:
        dis_type = request.GET['type']
        sense = request.GET['sense']
        base = request.GET['base']

    file_array = uploaded_files.objects.all()

    annotations_array = {}
    file_ids = []

    file_stats = {}

    for file in file_array:
        selected_file_name = file.filename
        file_ann = pdtbAnnotation.objects.filter(file=selected_file_name)

        stats = {}

        if base == 'dis-type':
            stats['title'] = 'Sense Distribution According to'
            stats['coloums'] = []
            stats['coloums'].append(['Senses', 'Counts'])
            if dis_type == 'ALL':
                for s in senses:
                    s_count = file_ann.filter(
                        Q(sense1__icontains=s) | Q(sense2__icontains=s)).count()

                    stats['coloums'].append([s, s_count])

                stats['title'] = stats['title'] + ' ALL Discourse Types'
            else:
                type_ann = file_ann.filter(
                    type=dis_type)
                for s in senses:
                    s_count = type_ann.filter(
                        Q(sense1__icontains=s) | Q(sense2__icontains=s)).count()

                    stats['coloums'].append([s, s_count])

                stats['title'] = stats['title'] + ' ' + dis_type + ' Discourse Type'

        elif base == 'sense':
            stats['title'] = 'Discourse Type Distribution in '
            stats['coloums'] = []
            stats['coloums'].append(['Discourse Types', 'Counts'])
            if sense == 'ALL':
                for t in types:
                    t_count = file_ann.filter(type=t).count()
                    stats['coloums'].append([t, t_count])

                stats['title'] = stats['title'] + ' ALL Relations'
            else:
                sense_ann = file_ann.filter(Q(sense1__icontains=sense) | Q(sense2__icontains=sense))
                for t in types:
                    t_count = sense_ann.filter(type=t).count()
                    stats['coloums'].append([t, t_count])

                stats['title'] = stats['title'] + ' Relations with ' + sense + ' Sense'

        file_stats[file.id] = stats

    return HttpResponse(json.dumps(file_stats))


'''
## DOWNLOAD
def download(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename=data.csv'
    writer = csv.writer(response)
    # name = pdtbAnnotation._name_
    # Write headers to CSV file
    fields = [f.name for f in pdtbAnnotation._meta.get_fields()]
    if fields:
        headers = fields
    else:
        headers = []
        for field in pdtbAnnotation._meta.get_fields():
            headers.append(field.name)
    writer.writerow(headers)
    # Write data to CSV file
    for obj in request.session['search_results']:
        row = []
        for field in headers:
            if field in headers:
                val = getattr(obj, field)
                if callable(val):
                    val = val()
                row.append(val.encode('UTF-8') if isinstance(val, basestring) else val)
        writer.writerow(row)
        # Return CSV file to browser as download
    return response
## DOWNLOAD
'''


def delete_file(request):
    filename = request.GET['filename']
    pdtbAnnotation.objects.filter(file=filename).delete()
    uploaded_files.objects.filter(filename=filename).delete()
    return HttpResponseRedirect('/upload/search_page/')


def download_excel(request):
    filename = request.GET['filename']

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename=' + filename + '(excel).csv'
    writer = csv.writer(response)
    # name = pdtbAnnotation._name_
    # Write headers to CSV file
    headers = ["Type", "Sense", "2nd Sense", "Annotation(raw)"]

    writer.writerow(headers)
    # Write data to CSV file
    for obj in request.session['search_results'][filename]:
        row = []
        argMap = dict()
        argMap[int(obj.connBeg)] = "%" + obj.conn + "%"
        argMap[int(obj.connBeg2)] = "%" + obj.conn2 + "%"
        argMap[int(obj.arg1Beg)] = "#" + obj.arg1 + "#"
        argMap[int(obj.arg2Beg)] = "*" + obj.arg2 + "*"
        argMap[int(obj.arg1Beg2)] = "#" + obj.arg12 + "#"
        argMap[int(obj.arg2Beg2)] = "*" + obj.arg22 + "*"

        orderedArgMap = collections.OrderedDict(sorted(argMap.items()))
        orderedArgMap.pop(-1, None)
        annotation = ""
        for a in orderedArgMap:
            annotation = annotation + " " + orderedArgMap[a]
        # print annotation
        val = getattr(obj, "type")
        if callable(val):
            val = val()
        row.append(val.encode('UTF-8') if isinstance(val, basestring) else val)
        val = getattr(obj, "sense1")
        if callable(val):
            val = val()
        row.append(val.encode('UTF-8') if isinstance(val, basestring) else val)
        val = getattr(obj, "sense2")
        if callable(val):
            val = val()
        row.append(val.encode('UTF-8') if isinstance(val, basestring) else val)
        row.append(annotation.encode('UTF-8') if isinstance(annotation, basestring) else annotation)

        writer.writerow(row)
        # Return CSV file to browser as download
    return response


def download_all(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename=all_files(excel).csv'
    writer = csv.writer(response)
    # name = pdtbAnnotation._name_
    # Write headers to CSV file
    headers = ["File", "Type", "Sense", "2nd Sense", "Annotation(raw)"]

    writer.writerow(headers)
    # Write data to CSV file
    for key in request.session['search_results']:
        for obj in request.session['search_results'][key]:
            row = []
            argMap = dict()
            argMap[int(obj.connBeg)] = "%" + obj.conn + "%"
            argMap[int(obj.connBeg2)] = "%" + obj.conn2 + "%"
            argMap[int(obj.arg1Beg)] = "#" + obj.arg1 + "#"
            argMap[int(obj.arg2Beg)] = "*" + obj.arg2 + "*"
            argMap[int(obj.arg1Beg2)] = "#" + obj.arg12 + "#"
            argMap[int(obj.arg2Beg2)] = "*" + obj.arg22 + "*"

            orderedArgMap = collections.OrderedDict(sorted(argMap.items()))
            orderedArgMap.pop(-1, None)
            annotation = ""
            for a in orderedArgMap:
                annotation = annotation + " " + orderedArgMap[a]
            # print annotation

            row.append(key.encode('UTF-8'))

            val = getattr(obj, "type")
            if callable(val):
                val = val()
            row.append(val.encode('UTF-8') if isinstance(val, basestring) else val)
            val = getattr(obj, "sense1")
            if callable(val):
                val = val()
            row.append(val.encode('UTF-8') if isinstance(val, basestring) else val)
            val = getattr(obj, "sense2")
            if callable(val):
                val = val()
            row.append(val.encode('UTF-8') if isinstance(val, basestring) else val)
            row.append(annotation.encode('UTF-8') if isinstance(annotation, basestring) else annotation)

            writer.writerow(row)
            # Return CSV file to browser as download
    return response


def download_pdtb(request):
    filename = request.GET['filename']

    response = HttpResponse(content_type='text/plain')
    response['Content-Disposition'] = 'attachment; filename=' + filename + '(pdtb).txt'

    types = ["Explicit", "Implicit", "EntRel", "AltLex", "NoRel"]
    for obj in request.session['search_results'][filename]:
        line = ""
        if str(obj.type) == types[0] or str(obj.type) == types[3]:
            line = str(obj.type) + "|" + handleDiscontniousSpan(obj.connBeg, obj.connEnd, obj.connBeg2,
                                                                obj.connEnd2) + "|Wr|Comm|Null|Null|||" \
                   + str(obj.sense1) + "|" + str(obj.sense2) + "|||||" + \
                   handleDiscontniousSpan(obj.arg1Beg, obj.arg1End, obj.arg1Beg2, obj.arg1End2) + \
                   "|Inh|Null|Null|Null||" + handleDiscontniousSpan(obj.arg2Beg, obj.arg2End, obj.arg2Beg2,
                                                                    obj.arg2End2) + \
                   "|Inh|Null|Null|Null||||||||DEFAULT|" + "\n"
        elif str(obj.type) == types[1]:
            line = str(obj.type) + "||Wr|Comm|Null|Null||" + obj.conn + "|" \
                   + str(obj.sense1) + "|" + str(obj.sense2) + "|||||" + \
                   handleDiscontniousSpan(obj.arg1Beg, obj.arg1End, obj.arg1Beg2, obj.arg1End2) + \
                   "|Inh|Null|Null|Null||" + handleDiscontniousSpan(obj.arg2Beg, obj.arg2End, obj.arg2Beg2,
                                                                    obj.arg2End2) + \
                   "|Inh|Null|Null|Null||||||||DEFAULT|" + "\n"
        else:
            line = str(obj.type) + "|||||||" + obj.conn + "||||||||" + str(obj.arg1Beg) + ".." + \
                   str(obj.arg1End) + "||||||" + str(obj.arg2Beg) + ".." + str(obj.arg2End) + \
                   "||||||||||||DEFAULT|" + "\n"
        response.write(line)
    return response


def handleDiscontniousSpan(beg1, end1, beg2, end2):
    if str(beg2) == str(-1):
        return str(beg1) + ".." + str(end1)
    else:
        return str(beg1) + ".." + str(end1) + ";" + str(beg2) + ".." + str(end2)


def get_connectives_wrt_language(request):
    if request.method == 'GET' and 'lang' in request.GET:
        lang = request.GET['lang']
        connectives = Dimlex.objects.filter(lang=lang)
        conn_list = [i.connective for i in connectives]
        return HttpResponse(json.dumps(conn_list))


def get_senses_wrt_connective(request):
    if request.method == 'GET' and 'connective' in request.GET:
        conn = request.GET['connective']
        conn = conn.split(",")
        selected_connective = Dimlex.objects.filter(connective__in=conn)
        pdtb3_relations = {}
        c = 0
        for i in selected_connective:
            word = []
            pdtb3_relations[i.connective] = word
            for s in i.metadata['syn']:
                # a = {"word": i.connective, "category": i.metadata['syn'][s]['cat'], "relation": i.metadata['syn'][s]['sem']}
                pdtb3_relations[i.connective].append(s)
            # pdtb3_relations = selected_connective.metadata['syn'][0]['sem']
            c = c + 1
        # return HttpResponse(json.dumps(pdtb3_relations))
        return HttpResponse(json.dumps(pdtb3_relations))


def get_senses_wrt_language(request):
    if request.method == 'GET' and 'lang' in request.GET:
        lang = request.GET['lang']
        connectives = Dimlex.objects.filter(lang=lang)

        relation = ""
        if lang in ['German', 'Portuguese', 'Italian']:
            relation = 'pdtb3_relation'
        elif lang in ['English']:
            relation = 'pdtb2_relation'
        elif lang in ['French']:
            relation = 'sdrt_relation'

        s_list = []
        for i in connectives:
            try:
                s_list.extend([s[relation][0]['sense'] for s in i.metadata['syn'][0]['sem']])
            except:
                print i.metadata['word']

        s_set = set(s_list)
        senses = list(s_set)

        return HttpResponse(json.dumps(senses))


def get_connectives_wrt_sense(request):
    if request.method == 'GET' and 'sense' in request.GET and 'lang' in request.GET:
        sens = request.GET['sense']
        lang = request.GET['lang']

        relation = ""
        if lang in ['German', 'Portuguese', 'Italian']:
            relation = 'pdtb3_relation'
        elif lang in ['English']:
            relation = 'pdtb2_relation'
        elif lang in ['French']:
            relation = 'sdrt_relation'

        path = "$.syn[*].sem[*]." + relation + "[*].sense"

        conns = Dimlex.objects.raw(
            'SELECT id, connective FROM portal_dimlex WHERE JSON_CONTAINS(metadata -> %s, JSON_ARRAY(%s))',
            [path, sens])
        conn_list = []
        for i in conns:
            conn_list.append(i.connective)
        return HttpResponse(json.dumps(conn_list))
