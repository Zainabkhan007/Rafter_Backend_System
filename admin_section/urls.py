from django.urls import path
from . import views
urlpatterns = [
    # Primary School Urls
    path("add_primary_school/",views.add_primary_school,name='add_primary_school'),
    path("primary_school/",views.primary_school,name='primary_school'),
    path("primary_school/<int:pk>/", views.delete_primary_school, name='delete_primary_school'),
    path('primary_school/search', views.PrimarySearch.as_view(), name='PrimarySearch'),

    path('primary_school/<int:school_id>/teacher/', views.add_and_get_teacher, name='add_and_get_teacher'), 
    path('primary_school/<int:school_id>/teacher/<int:teacher_id>/', views.update_delete_teacher, name='update_delete_teacher'),

    path('primary_school/<int:school_id>/student/', views.get_student_detail, name='get_student_detail'), 
    path('primary_school/<int:school_id>/student/<int:student_id>/', views.update_delete_student, name='update_delete_student'), 
    path('primary_student/search', views.StudentSearch.as_view(), name='StudentSearch'),
     # Secondary School Urls
    path("add_secondary_school/",views.add_secondary_school,name='add_secondary_school'),
    path("secondary_school/",views.secondary_school,name='secondary_school'),
    path("secondary_school/<int:pk>/", views.delete_secondary_school, name='delete_secondary_school'),


    path('add_secondary_student/<int:school_id>/', views.add_secondary_student, name='add_secondary_student'),
    path('secondary_school/<int:school_id>/student/<int:student_id>/', views.update_delete_secondary_student, name='update_delete_secondary_student'),




]