from django.contrib import admin
from .models import *
# Register your models here.
admin.site.register(PrimarySchool)
admin.site.register(Teacher)
admin.site.register(Student)
admin.site.register(SecondarySchool)
admin.site.register(SecondaryStudent)