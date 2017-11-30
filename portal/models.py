# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.db import models
from django_mysql.models import JSONField


class uploaded_files(models.Model):
    filename = models.CharField(max_length=500, default="")
    ann_file = models.FileField(upload_to='forms/')
    raw_file = models.FileField(upload_to='forms/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    user_id = models.CharField(max_length=1000, null=False, default="none")


class pdtbAnnotation(models.Model):
    type = models.CharField(max_length=30, null=False)
    conn = models.CharField(max_length=250, null=True)
    conn2 = models.CharField(max_length=250, null=True)
    connBeg = models.IntegerField(null=True)
    connEnd = models.IntegerField(null=True)
    connBeg2 = models.IntegerField(null=True)
    connEnd2 = models.IntegerField(null=True)
    # sense
    sense1 = models.CharField(max_length=500, null=True)
    sense2 = models.CharField(max_length=500, null=True)
    # file
    file = models.CharField(max_length=500, null=False, default="file")
    # arg1
    arg1 = models.TextField()
    arg12 = models.TextField(null=True)
    arg1Beg = models.IntegerField()
    arg1End = models.IntegerField()
    arg1Beg2 = models.IntegerField(null=True)
    arg1End2 = models.IntegerField(null=True)
    # arg2
    arg2 = models.TextField()
    arg22 = models.TextField(null=True)
    arg2Beg = models.IntegerField()
    arg2End = models.IntegerField()
    arg2Beg2 = models.IntegerField(null=True)
    arg2End2 = models.IntegerField(null=True)
    # language
    language = models.CharField(max_length=100, null=True)
    user_id = models.CharField(max_length=1000, null=False, default="none")


class ted_mdb_files(models.Model):
    filename = models.CharField(max_length=500, default="")
    raw_file = models.TextField()
    language = models.CharField(max_length=100, null=True)


class ted_mdb_annotation(models.Model):
    ann_id = models.CharField(max_length=30, null=False)
    type = models.CharField(max_length=30, null=False)
    conn = models.CharField(max_length=30, null=True)
    conn2 = models.CharField(max_length=30, null=True)
    connBeg = models.IntegerField(null=True)
    connEnd = models.IntegerField(null=True)
    connBeg2 = models.IntegerField(null=True)
    connEnd2 = models.IntegerField(null=True)
    # sense
    sense1 = models.CharField(max_length=500, null=True)
    sense2 = models.CharField(max_length=500, null=True)
    # file
    file = models.CharField(max_length=500, null=False, default="file")
    # arg1
    arg1 = models.TextField()
    arg12 = models.TextField(null=True)
    arg1Beg = models.IntegerField()
    arg1End = models.IntegerField()
    arg1Beg2 = models.IntegerField(null=True)
    arg1End2 = models.IntegerField(null=True)
    # arg2
    arg2 = models.CharField(max_length=50000)
    arg22 = models.TextField(null=True)
    arg2Beg = models.IntegerField()
    arg2End = models.IntegerField()
    arg2Beg2 = models.IntegerField(null=True)
    arg2End2 = models.IntegerField(null=True)
    # language
    language = models.CharField(max_length=100, null=True)


class ted_mdb_alignment(models.Model):
    fl_id = models.CharField(max_length=30, null=False, default="en-1")
    fl_file = models.CharField(max_length=500, null=False, default="file")
    sl_id = models.CharField(max_length=30, null=False, default="en-1")
    sl_file = models.CharField(max_length=500, null=False, default="file")


class Dimlex(models.Model):
    connective = models.CharField(max_length=255, blank=False)
    lang = models.CharField(max_length=255)
    metadata = JSONField()
