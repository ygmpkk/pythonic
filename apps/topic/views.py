#!/usr/bin/env python
# -*- coding: UTF-8 -*-
from apps.topic.forms import TopicForm, ReplyForm, ApplyForm, NodeEditForm
from apps.topic.models import Topic, Node, Reply, Description
from django.http import HttpResponseRedirect, Http404
from django.shortcuts import render
import datetime

def topic(request,topic_id):
    context = {}
    topic = Topic.objects.get(id=topic_id)
    context['topic'] = topic
    context['reply_list'] = Reply.objects.filter(topic=topic_id)
    context['form'] = ReplyForm()
    return render(request,'topic.html',context)

def node(request, node_slug):
    context = {}
    try:
        node = Node.objects.get(slug=node_slug)
    except Node.DoesNotExist:
        raise Http404
    context['node'] = node
    description = Description.objects.filter(node=node,active=True)
    if description:
        description = description[0]
    else:
        description = None
    context['description'] = description
    context['topics'] = Topic.objects.filter(node=node).order_by('-updated_on')
    context['form'] = TopicForm()
    return render(request,'node.html',context)

def node_edit(request,node_slug):
    context = {}
    try:
        node = Node.objects.get(slug=node_slug)
    except Node.DoesNotExist:
        raise Http404
    if request.method == 'GET':
        description = Description.objects.filter(node=node).order_by('-time')
        context['node'] = node
        context['description'] = description
        context['form'] = NodeEditForm()
        return render(request,'node_edit.html',context)
    
    form = NodeEditForm(request.POST)
    if form.is_valid():
        content = form.cleaned_data['content']
        Description.objects.filter(node=node).update(active=False)
        Description.objects.create(content=content,author=request.user,node=node,active=True)
    return HttpResponseRedirect('/node/'+node_slug)

def node_choose_description(request,node_slug):
    if request.method == 'GET':
        return HttpResponseRedirect('/node/'+node_slug)
    try:
        node = Node.objects.get(slug=node_slug)
    except Node.DoesNotExist:
        raise Http404
    description_id = request.POST['description_id']    
    try:
        description = Description.objects.get(id=description_id)
    except Description.DoesNotExist:
        raise Http404
    if description.node == node:
        Description.objects.filter(node=node).update(active=False)
        description.active = True
        description.save()
    else:
        raise Http404
    return HttpResponseRedirect('/node/'+node_slug)

def explore(request):
    context = {}
    
    return render(request,'explore.html',context)

def apply_node(request):
    if request.method == 'GET':
        return render(request,'apply.html')

def apply_new(request):
    context = {}
    if request.method == 'GET':
        form = ApplyForm()
        context['form'] = form
        return render(request,'apply_new.html',context)
    form = ApplyForm(request.POST)
    if form.is_valid():
        node = form.save(commit=False)
        node.author = request.user
        node.num_views = 0
        node.num_replies = 0
        node.updated_on = datetime.datetime.now()
        node.save()
    return render(request,'apply_success.html',context)

def topic_create(request, node_slug):
    if request.method == 'POST':
        try:
            node = Node.objects.get(slug=node_slug)
        except Node.DoesNotExist:
            raise Http404
        form = TopicForm(request.POST)
        if form.is_valid():
            topic = form.save(commit=False)
            topic.node = node
            topic.author = request.user
            topic.num_views = 0
            topic.num_replies = 0
            topic.updated_on = datetime.datetime.now()
            topic.save()
            node.num_topics += 1
            node.save()
            
    return HttpResponseRedirect('/node/'+node_slug)

def reply_create(request, topic_id):
    if request.method == 'POST':
        parent_id = request.POST['parent_id']
        form = ReplyForm(request.POST)
        if form.is_valid():
            reply = form.save(commit=False)
            reply.author = request.user
            reply.topic = Topic.objects.get(id=topic_id)
            reply.topic.num_replies += 1
            reply.topic.updated_on = datetime.datetime.now()
            reply.topic.last_reply = request.user
            reply.topic.save()
            if parent_id != '':
                reply.has_parent = True
                reply.parent = Reply.objects.get(pk=parent_id)
            reply.created_on = datetime.datetime.now()
            reply.save()
    return HttpResponseRedirect('/topic/'+topic_id)