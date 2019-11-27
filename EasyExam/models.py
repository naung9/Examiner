from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models
from . import apps


# Create your models here.
class ExamGroup(models.Model):
    def __str__(self):
        return "{} at {}".format(self.code, self.exam_date)
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=50)
    exam_date = models.DateField()


class Exam(models.Model):
    def __str__(self):
        return "{} {} {}".format(self.exam_group.code, self.name, self.exam_group.exam_date)

    name = models.CharField(max_length=100)
    examiners = models.CharField(max_length=200, blank=True, null=True, default=None)
    exam_date = models.DateField()
    duration = models.IntegerField(help_text="In Minutes")
    total_marks = models.IntegerField()
    exam_type = models.CharField(default="online", choices=(("on_venue", "On venue"), ("online", "Online")), max_length=15)
    exam_location = models.TextField(max_length=200, blank=True, null=True, default=None,
                                     help_text="Required Only For On venue exams")
    exam_group = models.ForeignKey(ExamGroup, on_delete=models.CASCADE)

    def clean(self):
        if self.exam_type == "on_venue" and not self.exam_location:
            raise ValidationError('Exam Location is required for On Venue Exams')
        super(Exam, self).clean()


class Question(models.Model):
    question_text = models.TextField()
    question_image = models.ImageField(upload_to=apps.EasyexamConfig.name+"/images", blank=True, null=True, default=None,
                                       help_text="This field is only required for questions with image")
    question_video = models.FileField(upload_to=apps.EasyexamConfig.name+"/videos", blank=True, null=True, default=None,
                                      help_text="This field is only required for questions with video")
    question_audio = models.FileField(upload_to=apps.EasyexamConfig.name+"/audios", blank=True, null=True, default=None,
                                      help_text="This field is only required for questions with audio")
    right_answer = models.CharField(max_length=200)
    right_answer_condition = models.CharField(max_length=10, default="choice",
                                              choices=(("exact", "Answer must be exactly the same"),
                                                        ("keyword", "Answer must include keywords"),
                                                        ("choice", "Choose one or more correct answers")))
    right_answer_splitter = models.CharField(max_length=10, default=",", blank=True, null=True,
                                             help_text="This field is only required for "
                                                       "choice and keyword conditions")
    max_mark = models.IntegerField()
    answer_type = models.CharField(max_length=50, default="single_choice", choices=(("text", "Text"), ("multi_text", "Multiple Text"),
                                                           ("single_choice", "Choose One"),
                                                           ("multiple_choice", "Multiple Choice")))
    answer_descriptions = models.TextField(help_text="Needed For Choice Answers.", blank=True, null=True, default=None)
    answer_values = models.CharField(max_length=10, help_text="Required For Choice Answers. e.g (A/B/C/D)",
                                     blank=True, null=True, default=None)
    answer_choice_splitter = models.CharField(max_length=10, default=",", blank=True, null=True,
                                              help_text="This Field Is Used to Split Answers")
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE)

    def get_multiple_answers_desc(self):
        if self.answer_type in ["single_choice", "multiple_choice"]:
            return self.answer_descriptions.split(self.answer_choice_splitter)
        return [self.answer_descriptions]

    def get_multiple_answers(self):
        answer_arr = []
        if self.answer_type in ["single_choice", "multiple_choice"]:
            for i, desc in enumerate(self.answer_descriptions.split(self.answer_choice_splitter)):
                answer = {"value": self.answer_values.split(self.answer_choice_splitter)[i], "desc": desc}
                answer_arr.append(answer)
        return answer_arr

    def get_multiple_answer_values(self):
        if self.answer_type in ["single_choice", "multiple_choice"]:
            return self.answer_values.split(self.answer_choice_splitter)
        return [self.answer_values]

    def get_multiple_right_answer(self):
        if self.right_answer_condition in ["keyword", "multiple_choice"]:
            return self.right_answer.split(self.right_answer_splitter)
        return [self.right_answer]

    def clean(self):
        if self.answer_type in ["single_choice", "multiple_choice"] and not self.answer_choice_splitter:
            raise ValidationError("Answer Choice Splitter is required for Choice Answer Types")
        elif self.answer_type in ["single_choice", "multiple_choice"] and self.answer_choice_splitter \
                and len(self.get_multiple_answer_values()) != len(self.get_multiple_answers_desc()):
            if not self.answer_descriptions:
                raise ValidationError("Answer Descriptions is required for Choice Answers")
            if not self.answer_values:
                raise ValidationError("Answer Values is required for Choice Answers")
            raise ValidationError("Answer Values Count and Answer Description Count Should Be The Same")
        if self.right_answer_condition in ["keyword", "choice"] and not self.right_answer_splitter:
            raise ValidationError("Right Answer Splitter is required for Choice and Keyword Answer Conditions")
        super(Question, self).clean()


class Examinee(models.Model):
    def __str__(self):
        return self.name
    name = models.CharField(max_length=100)
    registration_id = models.IntegerField()
    phone = models.CharField(max_length=30, null=True, blank=True, default=None)
    email = models.EmailField(max_length=50, unique=True, null=False, blank=False, default=None)
    registered_date = models.DateTimeField(auto_now_add=True)
    registering_exams = models.ManyToManyField(ExamGroup)


class AnswerRecord(models.Model):
    answer_time = models.DateTimeField(auto_now_add=True)
    given_answer = models.TextField()
    marks_achieved = models.IntegerField()
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
