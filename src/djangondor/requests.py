from django import forms
from typing import Dict
from django.http import JsonResponse
from django.db import models


def save_many_and_respond(*models:models.Model,success_status=200,error_status=400):
    try:
        for model in models:
            model.save()

    except Exception as e:
        return JsonResponse({"message": e.args[0]}, status=error_status)
    return JsonResponse({"message": 'saved'}, status=success_status)



def delete_and_respond(model: models.Model):
    '''
    Deletes a model and returns a 204 `JsonResponse` response
    '''
    try:
        model.delete()
        status = 204
        body = {}
    except:
        status = 400
        body = {"message": "Something is keeping you from deleting this object"}

    return JsonResponse(body, status=status)


def save_and_respond(
    model: models.Model,/, serialize_with=None, success_status=200, error_status=400,**kwargs
):
    '''
    Saves a model and return a a json response.
    '''
    try:
        for key,val in kwargs.items():
            setattr(model,key,val)
        model.save()
        return JsonResponse(
            {"message": "saved"} if not serialize_with else serialize_with(model).data,
            status=success_status,
        )
    except Exception as e:
        return JsonResponse({"message": e.args[0]}, status=error_status)


def format_form_errors(form: forms.ModelForm):
    errors = form.errors.as_data()
    keys = list(errors.keys())
    values = list(errors.values())
    items = [(keys[i], values[i][0].message) for i in range(0, len(errors))]
    return items


def form_error_response(form: forms.ModelForm, status=400):
    return JsonResponse(
        {"message": "%s %s" % format_form_errors(form)[0]}, status=status
    )



def process_form(
    form: forms.ModelForm, /, set_fields: Dict = None, error_status=400, respond=False
):
    """
    Return model that has been saved with `commit=False` when the form has no errors otherwise `None`
    and a `JsonResponse` object with the given `error_status` if the form had errors otherwise None
    The entries in `set_fields` are set on the model just after calling `save(commit=False)` on the form
    """
    if form.is_valid():
        model: models.Model = form.save(False)
        if set_fields and len(set_fields):
            for attr, val in set_fields.items():
                setattr(model, attr, val)
        if respond:
            try:
                model.save()
                form.save_m2m()
                return JsonResponse({"message": "saved"})
            except Exception as e:
                return JsonResponse({"message": e.args[0]}, status=500)
        return model, None
    elif respond:
        return form_error_response(form)
    return None, form_error_response(form, error_status)

