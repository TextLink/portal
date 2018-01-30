# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import codecs
import csv
import operator
from django.shortcuts import render, redirect
from django.http import HttpResponse

from portal.forms import *
from utils import *
from django.db.models import Q

from django.utils.crypto import get_random_string
import json
from django.utils.encoding import smart_unicode


def home(request):
    return HttpResponse("Welcome")


def upload_annotations(request):
    request.session.set_expiry(0)
    if 'user_id' not in request.session:
        user_id = get_random_string(length=32)
        request.session['user_id'] = user_id
    if request.method == 'POST':
        form = DocumentForm(request.POST, request.FILES)
        if form.is_valid():
            data = request.FILES['ann_file'].read()
            contents = smart_unicode(request.FILES['raw_file'].read())
            language = request.POST['language']
            populate_ann_db(request.FILES['ann_file'].name, data, contents, language, request.session['user_id'])
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
        #    text = smart_unicode(uploaded_files.objects.filter(filename=annotation['file'])[0].raw_file.read()).replace(
        #        "\n", "")
        with codecs.open(uploaded_files.objects.filter(filename=annotation['file'])[0].raw_file.path, 'r',
                         encoding='utf8') as f:
            text = f.read().replace("\n", "")

    if request.method == 'GET' and 'ted_mdb_annotation' in request.GET:
        annotation = \
            ted_mdb_annotation.objects.filter(ann_id=request.GET['ted_mdb_annotation']).values('connBeg', 'connEnd',
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
        annotations = ted_mdb_annotation.objects.filter(file=selected_file_name)
        annotation_list = dict()
        for a in annotations:
            annotation_list[a.ann_id] = a.conn + "(" + a.type + ")"

        connective_list = dict()
        connectives = ted_mdb_annotation.objects.filter(Q(type="Explicit") | Q(type="AltLex"),
                                                        file=selected_file_name).order_by('conn').distinct()
        for c in connectives:
            connective_list[c.conn] = c.conn + "(" + c.type + ")"

        result = dict()
        result['annotation_list'] = annotation_list
        result['connective_list'] = connective_list
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
            eng_annotation_list[a.ann_id] = a.conn + "(" + a.type + ")"

        result['eng_annotation_list'] = eng_annotation_list
        result['eng_text'] = eng_content
        return HttpResponse(json.dumps(result))

    # ON LOAD
    all_languages = ted_mdb_files.objects.values('language').distinct()
    first_doc = ted_mdb_files.objects.filter(language=all_languages.first()['language']).first()
    selected_language = first_doc.language

    if request.method == 'GET' and 'language' in request.GET:
        selected_language = request.GET['language']
        first_doc = ted_mdb_files.objects.filter(language=selected_language).first()

    selected_file_name = first_doc.filename
    selected_file_content = first_doc.raw_file
    documents = ted_mdb_files.objects.filter(language=selected_language)

    annotations = ted_mdb_annotation.objects.filter(file=selected_file_name)
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
                                            'documents': documents, 'annotations': annotations,
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
    annotations = ted_mdb_annotation.objects.filter(file=selected_file_name)
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

    if '2150' in request.GET['file']:
        selected_eng_file_name = "talk_2150_en.txt"
    else:
        selected_eng_file_name = "talk_2009_en.txt"
    for a in annotations:
        annotation_list[a.ann_id] = a.conn + "(" + a.type + ")" + " | " + a.sense1 + " | " + a.sense2

    result = dict()
    result['text'] = content
    result['annotation_list'] = annotation_list

    return HttpResponse(json.dumps(annotation_list))


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
            eng_annotation = ted_mdb_annotation.objects.filter(ann_id=eng_eq.values('fl_id').first()['fl_id'],
                                                               file=selected_eng_file_name)
            result = dict()
            result[eng_annotation[0].ann_id] = eng_annotation[0].conn + "(" + eng_annotation[0].type + ")" \
                                               + " | " + eng_annotation[0].sense1 + " | " + eng_annotation[0].sense2

            return HttpResponse(json.dumps(result))
        except:
            pass


####### TED - MDB  #######


def search_sense_rest(request):
    if request.method == 'POST':
        return redirect('upload_annotations.html')

    selected_file_name = request.GET['file']
    selected_file = uploaded_files.objects.filter(filename=selected_file_name).first()
    content = selected_file.raw_file.read()
    annotation_list = dict()
    annotations = pdtbAnnotation.objects.filter(file=selected_file_name)
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

    for a in annotations:
        annotation_list[a.id] = a.conn + "(" + a.type + ")" + " | " + a.sense1 + " | " + a.sense2
    result = dict()
    result['text'] = content
    result['annotation_list'] = annotation_list
    request.session['search_results'] = annotations
    return HttpResponse(json.dumps(result))


# ONLOAD
def search_page_rest(request):
    documents = uploaded_files.objects.filter()

    if request.method == 'GET' and 'file' in request.GET:
        selected_file_name = request.GET['file']
        selected_file = uploaded_files.objects.filter(filename=selected_file_name).first()
        content = selected_file.raw_file.read()
        annotations = pdtbAnnotation.objects.filter(file=selected_file_name)
        annotation_list = dict()
        for a in annotations:
            annotation_list[a.id] = a.conn + "(" + a.type + ") | " + a.sense1 + "|" + a.sense2
        connective_list = dict()
        connectives = pdtbAnnotation.objects.filter(Q(type="Explicit") | Q(type="AltLex"),
                                                    file=selected_file_name).order_by('conn').distinct()
        for c in connectives:
            connective_list[c.conn] = c.conn + "(" + c.type + ")"

        result = dict()
        result['annotation_list'] = annotation_list
        result['connective_list'] = connective_list
        result['text'] = content
        request.session['search_results'] = annotations

        return HttpResponse(json.dumps(result))

    if request.method == 'POST':
        return redirect('upload_annotations.html')

    # ON LOAD
    first = uploaded_files.objects.filter().first()
    selected_file_name = first.filename
    selected_file = uploaded_files.objects.filter(filename=selected_file_name).first()
    annotations = pdtbAnnotation.objects.filter(file=selected_file_name)
    senses = pdtbAnnotation.objects.filter(file=selected_file_name).values('sense1',
                                                                           'sense2').distinct()
    connectives = pdtbAnnotation.objects.filter(file=selected_file_name).values(
        'conn', 'conn2',
        'type').distinct()
    connective_array = prepareConnList(connectives)

    request.session['search_results'] = annotations

    sense_array = prepareSenseList(senses)
    return render(request, 'search_page.html', {'documents': documents, 'annotations': annotations,
                                                'selectedFile': selected_file,
                                                'selectedFileName': selected_file_name,
                                                'senses': sense_array,
                                                'connective_array': connective_array
                                                })


####### SEARCH ##############


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


def get_connectives_wrt_language(request):
    if request.method == 'GET' and 'lang' in request.GET:
        lang = request.GET['lang']
        connectives = Dimlex.objects.filter(lang=lang)
        conn_list = [i.connective for i in connectives]
        return HttpResponse(json.dumps(conn_list))


def get_senses_wrt_connective(request):
    if request.method == 'GET' and 'connective' in request.GET and 'lang' in request.GET:
        conn = request.GET['connective']
        conn = conn.split(",")
        lang = request.GET['lang']
        selected_connective = Dimlex.objects.filter(
            reduce(operator.or_, (Q(connective=c) for c in conn)), lang=lang
        )
        pdtb3_relations = []
        for i in selected_connective:
            a = {"word": i.connective, "relation": i.metadata['syn'][0]['sem']}
            pdtb3_relations.append(a)
        # pdtb3_relations = selected_connective.metadata['syn'][0]['sem']
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
