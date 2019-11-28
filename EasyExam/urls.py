from django.urls import path
from . import views

app_name = "EasyExam"

urlpatterns = [
    path('exam/<int:id>', views.take_exam, name="take_exam"),
    path('login', views.login, name="login"),
    path('', views.home, name="home"),
    path('logout', views.logout, name="logout"),
    path('evaluate/<int:exam_id>', views.eval_results, name="evaluate"),
    path('result/<int:exam_id>', views.review_results, name="exam_results"),
]