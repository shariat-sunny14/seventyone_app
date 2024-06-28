import json
import sys
from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.db.models import Q
from django.db import transaction
from django.contrib import messages
from item_setup.models import items
from store_setup.models import store
from django.contrib.auth.decorators import login_required
from .models import module_list, module_type, feature_list
from django.contrib.auth import get_user_model
User = get_user_model()

# module setup


@login_required()
def moduleSetupAPI(request):
    list = module_list.objects.all()
    Mtype = module_type.objects.all()
    feature = feature_list.objects.all()
    context = {
        'list': list,
        'Mtype': Mtype,
        'feature': feature,
    }
    return render(request, 'module_setup/module_setup.html', context)


@login_required()
def moduleManageAPI(request):
    module = {}
    if request.method == 'GET':
        data = request.GET
        module_id = ''
        if 'module_id' in data:
            module_id = data['module_id']
        if module_id.isnumeric() and int(module_id) > 0:
            module = module_list.objects.filter(module_id=module_id).first()

    context = {
        'module': module
    }
    return render(request, 'module_setup/module.html', context)


@login_required
def saveModuleAPI(request):
    data = request.POST
    resp = {'status': 'failed'}

    module_id = ''
    if 'module_id' in data:
        module_id = data['module_id']
    if module_id.isnumeric() and int(module_id) > 0:
        # check module no
        checkModule_no = module_list.objects.exclude(module_id=module_id).filter(
            module_no=data['module_no']).all()
        # check module name
        checkModule_name = module_list.objects.exclude(module_id=module_id).filter(
            module_name=data['module_name']).all()
        # check module code
        checkModule_code = module_list.objects.exclude(module_id=module_id).filter(
            module_code=data['module_code']).all()
    else:
        # check module no
        checkModule_no = module_list.objects.filter(
            module_no=data['module_no']).all()
        # check module name
        checkModule_name = module_list.objects.filter(
            module_name=data['module_name']).all()
        # check module code
        checkModule_code = module_list.objects.filter(
            module_code=data['module_code']).all()
    if len(checkModule_no) > 0:
        return JsonResponse({'success': False, 'errmsg': 'Module No ' + "' " + data['module_no'] + " '" + ' already exists'})
    #
    elif len(checkModule_name) > 0:
        return JsonResponse({'success': False, 'errmsg': 'Module Name ' + "' " + data['module_name'] + " '" + ' already exists'})
    #
    elif len(checkModule_code) > 0:
        return JsonResponse({'success': False, 'errmsg': 'Module Code ' + "' " + data['module_code'] + " '" + ' already exists'})
    #
    else:
        try:
            with transaction.atomic():
                if (data['module_id']).isnumeric() and int(data['module_id']) > 0:
                    # update module data
                    save_module = module_list.objects.filter(module_id=data['module_id']).update(module_no=data['module_no'], module_name=data['module_name'],
                                                                                                 module_code=data['module_code'], is_active=data['is_active'], ss_modifier=request.user)
                else:
                    # save module data
                    save_module = module_list(module_no=data['module_no'], module_name=data['module_name'], module_code=data['module_code'],
                                              is_active=data['is_active'], ss_creator=request.user)
                    save_module.save()
                resp['status'] = 'success'
                return JsonResponse({'success': True, 'msg': 'Successful'})
        except:
            resp['status'] = 'failed'
    return HttpResponse(json.dumps(resp), content_type="application/json")


@login_required
def deleteModuleAPI(request):
    data = request.POST
    resp = {'status': ''}
    try:
        module_list.objects.filter(module_id=data['module_id']).delete()
        resp['status'] = 'success'
        return JsonResponse({'success': True, 'msg': 'Module Successfully deleted.'})
    except:
        resp['status'] = 'failed'
    return HttpResponse(json.dumps(resp), content_type="application/json")


# module type setup
@login_required()
def moduleTyteManageAPI(request):
    moduleType = {}
    modules = module_list.objects.filter(is_active=1).all()
    if request.method == 'GET':
        data = request.GET
        type_id = ''
        if 'type_id' in data:
            type_id = data['type_id']
        if type_id.isnumeric() and int(type_id) > 0:
            moduleType = module_type.objects.filter(type_id=type_id).first()

    context = {
        'modules': modules,
        'moduleType': moduleType,
    }

    return render(request, 'module_setup/module_type.html', context)


@login_required
def saveModuleTyteAPI(request):
    data = request.POST
    resp = {'status': 'failed'}
    type_id = ''
    if 'type_id' in data:
        type_id = data['type_id']
    if type_id.isnumeric() and int(type_id) > 0:
        checktype_no = module_type.objects.exclude(
            type_id=type_id).filter(type_no=data['type_no']).all()
        #
        checktype_name = module_type.objects.exclude(
            type_id=type_id).filter(type_name=data['type_name']).all()
        #
        checktype_code = module_type.objects.exclude(
            type_id=type_id).filter(type_code=data['type_code']).all()
        #
        checktype_icon = module_type.objects.exclude(
            type_id=type_id).filter(type_icon=data['type_icon']).all()
    else:
        checktype_no = module_type.objects.filter(
            type_no=data['type_no']).all()
        #
        checktype_name = module_type.objects.filter(
            type_name=data['type_name']).all()
        #
        checktype_code = module_type.objects.filter(
            type_code=data['type_code']).all()
        #
        checktype_icon = module_type.objects.filter(
            type_icon=data['type_icon']).all()
    if len(checktype_no) > 0:
        return JsonResponse({'success': False, 'errmsg': 'Type No ' + "' " + data['type_no'] + " '" + ' already exists'})
    #
    elif len(checktype_name) > 0:
        return JsonResponse({'success': False, 'errmsg': 'Type Name ' + "' " + data['type_name'] + " '" + ' already exists'})
    #
    elif len(checktype_code) > 0:
        return JsonResponse({'success': False, 'errmsg': 'Type Code ' + "' " + data['type_code'] + " '" + ' already exists'})
    #
    elif len(checktype_icon) > 0:
        return JsonResponse({'success': False, 'errmsg': 'Type Icon ' + "' " + data['type_icon'] + " '" + ' already exists'})
    else:
        moduleData = module_list.objects.filter(
            module_id=data['module_id']).first()
        try:
            with transaction.atomic():
                if (data['type_id']).isnumeric() and int(data['type_id']) > 0:
                    save_type = module_type.objects.filter(type_id=data['type_id']).update(type_no=data['type_no'], type_name=data['type_name'],
                                                                                           type_code=data['type_code'], module_id=moduleData,
                                                                                           type_icon=data['type_icon'], is_active=data['type_status'], ss_modifier=request.user)
                else:
                    save_type = module_type(type_no=data['type_no'], type_name=data['type_name'], type_code=data['type_code'],
                                            module_id=moduleData, type_icon=data['type_icon'], is_active=data['type_status'], ss_creator=request.user)
                    save_type.save()
                resp['status'] = 'success'
                return JsonResponse({'success': True, 'msg': 'Successful'})
        except:
            resp['status'] = 'failed'
    return HttpResponse(json.dumps(resp), content_type="application/json")


@login_required
def deleteModuleTypeAPI(request):
    data = request.POST
    resp = {'status': ''}
    try:
        module_type.objects.filter(type_id=data['type_id']).delete()
        resp['status'] = 'success'
        return JsonResponse({'success': True, 'msg': 'delete Successfully.'})
    except:
        resp['status'] = 'failed'
    return HttpResponse(json.dumps(resp), content_type="application/json")


# module feature setup
@login_required()
def moduleFeatureManageAPI(request):
    moduleFeature = {}
    modules = module_list.objects.filter(is_active=1).all()
    mod_type = module_type.objects.filter(is_active=1).all()
    if request.method == 'GET':
        data = request.GET
        feature_id = ''
        if 'feature_id' in data:
            feature_id = data['feature_id']
        if feature_id.isnumeric() and int(feature_id) > 0:
            moduleFeature = feature_list.objects.filter(
                feature_id=feature_id).first()

    context = {
        'modules': modules,
        'mod_type': mod_type,
        'moduleFeature': moduleFeature,
    }

    return render(request, 'module_setup/features.html', context)


@login_required
def saveFeaturesAPI(request):
    data = request.POST
    resp = {'status': 'failed'}
    feature_id = ''
    if 'feature_id' in data:
        feature_id = data['feature_id']
    if feature_id.isnumeric() and int(feature_id) > 0:
        checkfeature_no = feature_list.objects.exclude(
            feature_id=feature_id).filter(feature_no=data['feature_no']).all()
        #
        checkfeature_name = feature_list.objects.exclude(
            feature_id=feature_id).filter(feature_name=data['feature_name']).all()
        #
        checkfeature_code = feature_list.objects.exclude(
            feature_id=feature_id).filter(feature_code=data['feature_code']).all()
        #
        checkpage_link = feature_list.objects.exclude(
            feature_id=feature_id).filter(feature_page_link=data['feature_page_link']).all()
        #
        checkfeature_icon = feature_list.objects.exclude(
            feature_id=feature_id).filter(feature_icon=data['feature_icon']).all()
    else:
        checkfeature_no = feature_list.objects.filter(
            feature_no=data['feature_no']).all()
        #
        checkfeature_name = feature_list.objects.filter(
            feature_name=data['feature_name']).all()
        #
        checkfeature_code = feature_list.objects.filter(
            feature_code=data['feature_code']).all()
        #
        checkpage_link = feature_list.objects.filter(
            feature_page_link=data['feature_page_link']).all()
        #
        checkfeature_icon = feature_list.objects.filter(
            feature_icon=data['feature_icon']).all()
    if len(checkfeature_no) > 0:
        return JsonResponse({'success': False, 'errmsg': 'Feature No ' + "' " + data['feature_no'] + " '" + ' already exists'})
    #
    elif len(checkfeature_name) > 0:
        return JsonResponse({'success': False, 'errmsg': 'Feature Name ' + "' " + data['feature_name'] + " '" + ' already exists'})
    #
    elif len(checkfeature_code) > 0:
        return JsonResponse({'success': False, 'errmsg': 'Feature Code ' + "' " + data['feature_code'] + " '" + ' already exists'})
    #
    elif len(checkpage_link) > 0:
        return JsonResponse({'success': False, 'errmsg': 'Page Link ' + "' " + data['feature_page_link'] + " '" + ' already exists'})
    #
    elif len(checkfeature_icon) > 0:
        return JsonResponse({'success': False, 'errmsg': 'Feature Icon ' + "' " + data['feature_icon'] + " '" + ' already exists'})
    else:
        moduleData = module_list.objects.filter(
            module_id=data['module_id']).first()
        typeData = module_type.objects.filter(type_id=data['type_id']).first()
        try:
            with transaction.atomic():
                if (data['feature_id']).isnumeric() and int(data['feature_id']) > 0:
                    save_feature = feature_list.objects.filter(feature_id=data['feature_id']).update(feature_no=data['feature_no'], feature_name=data['feature_name'], feature_type=data['feature_type'], serial_no=data['serial_no'],
                                                                                                     feature_code=data['feature_code'], feature_page_link=data['feature_page_link'], module_id=moduleData, type_id=typeData, feature_icon=data['feature_icon'], is_active=data['feature_status'], ss_modifier=request.user)
                else:
                    save_feature = feature_list(feature_no=data['feature_no'], feature_name=data['feature_name'], feature_type=data['feature_type'], serial_no=data['serial_no'],
                                                feature_code=data['feature_code'], feature_page_link=data['feature_page_link'], module_id=moduleData, type_id=typeData, feature_icon=data['feature_icon'], is_active=data['feature_status'], ss_creator=request.user)
                    save_feature.save()
                resp['status'] = 'success'
                return JsonResponse({'success': True, 'msg': 'Successful'})
        except:
            resp['status'] = 'failed'
    return HttpResponse(json.dumps(resp), content_type="application/json")


@login_required
def deleteFeatureAPI(request):
    data = request.POST
    resp = {'status': ''}
    try:
        feature_list.objects.filter(feature_id=data['feature_id']).delete()
        resp['status'] = 'success'
        return JsonResponse({'success': True, 'msg': 'delete Successfully.'})
    except:
        resp['status'] = 'failed'
    return HttpResponse(json.dumps(resp), content_type="application/json")
