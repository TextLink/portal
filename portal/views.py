# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render

from django.http import HttpResponse


def hello(request):
    text = """<h1>Welcome to TextLink Portal</h1>"""
    return HttpResponse(text)


def hello_html(request):
    return render(request, "hello.html", {})
