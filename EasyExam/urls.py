from django.urls import path
from . import views

app_name = "EasyExam"

urlpatterns = [
    path('exam/<int:id>', views.take_exam, name="take_exam"),
    path('login', views.login, name="login"),
    path('', views.home, name="home"),
    path('logout', views.logout, name="logout")
]