import datetime

import pytz
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponseForbidden
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.views.decorators.http import require_POST

from . import models


# Create your views here.
def take_exam(request, id):
    if not request.session.get("email", None):
        return redirect(reverse("EasyExam:login"))
    
    try:
        examinee = models.Examinee.objects.get(email=request.session["email"])
        exam = models.Exam.objects.get(id=id, exam_group__examinee__email=request.session["email"], exam_date=datetime.datetime.now(tz=pytz.timezone("Asia/Rangoon")))
        return render(request, "EasyExam/TakeExam.html", {"exam": exam, "questions": exam.question_set.all(), "examinee": examinee})
    except ObjectDoesNotExist as e:
        return HttpResponseForbidden()


def login(request):
    if request.session.get("email", None):
        return redirect(reverse("EasyExam:home"))
    if request.method == "GET":
        return render(request, "EasyExam/Login.html", {})
    else:
        email = request.POST.get("email", "")
        reg_no = request.POST.get("reg_no", "")
        try:
            examinee = models.Examinee.objects.get(email=email)
            if examinee.registration_id != int(reg_no):
                print("Given {}, Existing {}", examinee.registration_id, reg_no)
                return render(request, "EasyExam/Login.html", {"error": "Registration Number is wrong"})
            request.session["email"] = email
        except ObjectDoesNotExist as e:
            return render(request, "EasyExam/Login.html", {"error": "Examinee with given email not found"})
        return redirect(reverse("EasyExam:home"))


def logout(request):
    request.session.flush()
    return redirect(reverse("EasyExam:login"))


def home(request):
    if not request.session.get("email", None):
        return redirect(reverse("EasyExam:login"))
    examinee = models.Examinee.objects.get(email=request.session["email"])
    return render(request, "EasyExam/Home.html",
                  {"exam_groups": examinee.registering_exams.filter(exam_date__gt=datetime.datetime.now(tz=pytz.timezone("Asia/Rangoon"))).order_by('-exam_date')[:10]})
