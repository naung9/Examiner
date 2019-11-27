from django.contrib import admin


class CustomAdminSite(admin.AdminSite):
    site_header = "Exam Management"
    site_title = "Exam Administration"

