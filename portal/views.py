# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.shortcuts import render, redirect
from django.http import HttpResponse

from portal.forms import *
from utils import *

import json


def home(request):
    documents = uploaded_files.objects.all()
    return render(request, 'home.html', {'documents': documents})


def dnm(request):
    return render(request, 'dnm.html', )


def model_form_upload(request):
    if request.method == 'POST':
        form = DocumentForm(request.POST, request.FILES)
        if form.is_valid():
            data = request.FILES['ann_file'].read()
            contents = request.FILES['raw_file'].read()
            populate_ann_db(request.FILES['ann_file'].name, data, contents)
            file_object = form.save(commit=False)
            file_object.filename = request.FILES['ann_file'].name
            file_object.save()
        return redirect('search_page.html')
    else:
        form = DocumentForm()
    return render(request, 'model_form_upload.html', {
        'form': form
    })


def search_page_rest(request):
    documents = uploaded_files.objects.all()

    if request.method == 'GET' and 'file' in request.GET and 'sense' not in request.GET:
        selected_file_name = request.GET['file']
        selected_file = uploaded_files.objects.filter(filename=selected_file_name).first()
        content = selected_file.raw_file.read()
        annotations = pdtbAnnotation.objects.filter(file=selected_file_name)
        annotation_list = dict()
        annotation_list["text"] = content
        for a in annotations:
            annotation_list[a.id] = a.conn + "(" + a.type + ")"
        return HttpResponse(json.dumps(annotation_list))

    if request.method == 'GET' and 'file' in request.GET and 'sense' in request.GET:
        selected_file_name = request.GET['file']
        sense = request.GET['sense']
        selected_file = uploaded_files.objects.filter(filename=selected_file_name).first()
        content = selected_file.raw_file.read()
        annotations = pdtbAnnotation.objects.raw(
            '''SELECT id, conn, type FROM portal_pdtbannotation p 
            WHERE p.sense1 = %s and p.file = %s''', [sense, selected_file_name])
        annotation_list = dict()
        annotation_list["text"] = content
        for a in annotations:
            annotation_list[a.id] = a.conn + "(" + a.type + ")"
        return HttpResponse(json.dumps(annotation_list))

    if request.method == 'POST':
        return redirect('model_form_upload.html')

    # ON LOAD
    first = uploaded_files.objects.first()
    selected_file_name = first.filename
    selected_file = uploaded_files.objects.filter(filename=selected_file_name).first()
    annotations = pdtbAnnotation.objects.filter(file=selected_file_name)
    senses = pdtbAnnotation.objects.values('sense1', 'sense2').distinct()
    sense_array = prepareSenseList(senses)
    return render(request, 'search_page.html', {'documents': documents, 'annotations': annotations,
                                                'selectedFile': selected_file,
                                                'selectedFileName': selected_file_name,
                                                'senses': sense_array
                                                })


def query(request):
    return render(request, "query.html", {})


def get_connectives_wrt_language(request):
    if request.method == 'GET' and 'lang' in request.GET:
        lang = request.GET['lang']
        connectives = Dimlex.objects.filter(lang=lang)
        conn_list = [i.connective for i in connectives]
        return HttpResponse(json.dumps(conn_list))


def get_senses_wrt_connective(request):
    if request.method == 'GET' and 'connective' in request.GET and 'lang' in request.GET:
        conn = request.GET['connective']
        lang = request.GET['lang']
        selected_connective = Dimlex.objects.filter(connective=conn, lang=lang)
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


'''
def dimlex_rest(request):
    try:

        if request.method == 'GET' and 'connective' in request.GET:
            conn = request.GET['connective']
            lang = request.GET['lang']
            selected_connective = Dimlex.objects.filter(connective=conn, lang=lang)
            pdtb3_relations = []
            for i in selected_connective:
                a = {"word": i.connective, "relation": i.metadata['syn'][0]['sem']}
                pdtb3_relations.append(a)
            # pdtb3_relations = selected_connective.metadata['syn'][0]['sem']
            return HttpResponse(json.dumps(pdtb3_relations))

        if request.method == 'GET' and 'sense' in request.GET:
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

    except:
        message = {"Message": "Nothing to Show"}
        return HttpResponse(json.dumps(message))
'''

'''
def dimlex(request):
    langs = ['German', 'Portuguese', 'Italian', 'English', 'French']

    connectives = Dimlex.objects.all()
    s_list = []
    for i in connectives:
        try:
            s_list.extend([s['pdtb3_relation'][0]['sense'] for s in i.metadata['syn'][0]['sem']])
        except:
            print i.metadata['word']

    s_set = set(s_list)
    senses = list(s_set)

    if request.method == 'POST' and 'connective' in request.POST:
        selected_conn = request.POST['connective']
        selected_lang = request.POST['lang']
        selected_connective = Dimlex.objects.filter(connective=selected_conn, lang=selected_lang)
        pdtb3_relations = []
        for i in selected_connective:
            a = {"word": i.connective, "relation": i.metadata['syn'][0]['sem']}
            pdtb3_relations.append(a)
        return render(request, 'search.html', {
            'pdtb3_relations': pdtb3_relations,
            'connectives': connectives,
            'senses': senses,
            'langs': langs
        })

    if request.method == 'POST' and 'sense' in request.POST:
        selected_sen = request.POST['sense']
        # conns = Dimlex.objects.filter(metadata__syn__0__sem____pdtb3_relations__0={"sense": "contrast"})
        conns = Dimlex.objects.raw(
            'SELECT id, connective FROM portal_dimlex WHERE JSON_CONTAINS(metadata -> "$.syn[*].sem[*].pdtb3_relation[*].sense", JSON_ARRAY(%s))',
            [selected_sen])
        conn_list = []
        for i in conns:
            conn_list.append(i.connective)

        return render(request, 'search.html', {
            'connectives': connectives,
            'senses': senses,
            'conn_list': conn_list
        })

    return render(request, 'search.html', {
        'connectives': connectives,
        'senses': senses
    })
'''
