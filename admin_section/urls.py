from django.urls import path
from . import views
# from .views import StudentSearchView
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
# Category
    path("get_category/",views.get_category,name='get_category'),
#    Menu
    path("add_menu/",views.add_menu,name='add_menu'),
    path("get_complete_menu/",views.get_complete_menu,name='get_complete_menu'),
    path("edit_menu/<int:id>/",views.edit_menu,name='edit_menu'),
    path("add_menu_item/",views.add_menu_item,name='add_menu_item'),

    # View Registered Students
    path("view_students/",views.view_students,name='view_students'),
    path("edit_student/<int:student_id>/",views.edit_student,name='edit_student'),
   



]
