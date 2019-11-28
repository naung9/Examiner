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
        exam = models.Exam.objects.get(id=id, question__answerrecord=None)
        return render(request, "EasyExam/TakeExam.html", {"exam": exam, "questions": exam.question_set.all(), "examinee": examinee})
    except ObjectDoesNotExist as e:
        return HttpResponseForbidden()


def review_results(request, exam_id):
    if not request.session.get("email", None):
        return redirect(reverse("EasyExam:login"))
    exam = get_object_or_404(models.Exam, id=exam_id)
    results = models.AnswerRecord.objects.filter(question__exam_id=exam.id, examinee__email=request.session["email"])
    return render(request, "EasyExam/ResultsComparison.html", {"results": results, "exam": exam})


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
    registered_exam_groups = examinee.registering_exams.all()
    exam_groups = []
    for exam_group in registered_exam_groups:
        exams = []
        for exam in exam_group.exam_set.all():
            results = models.AnswerRecord.objects.filter(question__exam_id=exam.id, examinee__email=request.session["email"])
            total_marks = 0
            exam_obj = {
                "completed": False,
                "id": exam.id,
                "name": exam.name,
                "date": exam.exam_start_time
            }
            if results.count() != 0:
                exam_obj["completed"] = True
                for result in results:
                    total_marks += result.marks_achieved
                grading_standards = exam.grading_standards.split(",")
                grade = "Fail"
                for standard in grading_standards:
                    gs = standard.split(":")
                    condition = eval(gs[1])
                    print(condition)
                    if condition:
                        grade = gs[0]
                exam_obj["achieved_marks"] = total_marks
                exam_obj["grade"] = grade
            exam_obj["total_marks"] = exam.total_marks
            exams.append(exam_obj)
        exam_group_obj = {
            "id": exam_group.id,
            "name": exam_group.name,
            "date": exam_group.exam_date,
            "exams": exams
        }
        exam_groups.append(exam_group_obj)

    return render(request, "EasyExam/Home.html",
                  {"upcoming_exam_groups": examinee.registering_exams.filter(exam_date__gte=datetime.datetime.now(tz=pytz.timezone("Asia/Rangoon"))).order_by('-exam_date')[:10],
                   "registered_exam_groups": exam_groups})


@require_POST
def eval_results(request, exam_id):
    if not request.session.get("email", None):
        return redirect(reverse("EasyExam:login"))
    exam = get_object_or_404(models.Exam, id=exam_id)
    examinee = models.Examinee.objects.get(email=request.session["email"])
    answer_time = datetime.datetime.now(tz=pytz.timezone("Asia/Rangoon"))
    total_marks = 0
    results = []

    for question in exam.question_set.all():
        answer_list = request.POST.getlist("question{}".format(question.id), [])
        print(answer_list)
        if not answer_list:
            result = models.AnswerRecord(answer_time=answer_time, examinee_id=examinee.id,
                                         given_answer="",
                                         marks_achieved=0, question=question)
            results.append(result)
            continue
        if question.right_answer_condition == "exact":
            achieved_mark = question.max_mark if answer_list[0].lower() == question.right_answer.lower() else 0
            total_marks += achieved_mark
        elif question.right_answer_condition == "keyword":
            right_answers = question.get_multiple_right_answer()
            achieved_mark = 0
            mark = question.max_mark / len(right_answers)
            for right_answer in right_answers:
                if right_answer.lower() in answer_list[0].lower():
                    achieved_mark += mark
                    total_marks += mark
        else:
            right_answers = question.get_multiple_right_answer()
            right_answers.sort()
            given_answers = answer_list
            answer_list.sort()
            mark = question.max_mark / len(right_answers)
            achieved_mark = 0
            for index, right_answer in enumerate(right_answers):
                if index < len(given_answers) and right_answer == given_answers[index]:
                    achieved_mark += mark
                    total_marks += mark
        result = models.AnswerRecord(answer_time=answer_time, examinee_id=examinee.id,
                                     given_answer=question.answer_choice_splitter.join(answer_list), marks_achieved=achieved_mark, question=question)
        results.append(result)
    models.AnswerRecord.objects.bulk_create(results)
    grading_standards = exam.grading_standards.split(",")
    grade = "Fail"
    for standard in grading_standards:
        gs = standard.split(":")
        condition = eval(gs[1])
        print(condition)
        if condition:
            grade = gs[0]
    inform_result = {
        "achieved": total_marks,
        "grade": grade,
        "exam": exam
    }
    return render(request, "EasyExam/ShowResult.html", inform_result)