from django.urls import path,include
from . import views
# from .views import StudentSearchView
urlpatterns = [


    path("register/",views.register,name='register'),
    path('login/', views.login,name='login'),
    path('password_reset/', include('django_rest_passwordreset.urls', namespace='password_reset')),
    path('admin_login/', views.admin_login,name='admin_login'),
    # path('get_parent_by_id/<int:parent_id>/', views.get_parent_by_id, name='get_parent_by_id'),
    # path('get_staff_by_id/<int:staff_id>/', views.get_staff_by_id, name='get_staff_by_id'),
    # path('get_student_by_id/<int:student_id>/', views.get_student_by_id, name='get_student_by_id'),

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
    path("activate_cycle/",views.activate_cycle,name='activate_cycle'),

    path("edit_menu/<int:id>/",views.edit_menu,name='edit_menu'),
    path("get_cycle_names/",views.get_cycle_names,name='get_cycle_names'),
    path("add_menu_item/",views.add_menu_item,name='add_menu_item'),
    path("get_menu_items/",views.get_menu_items,name='get_menu_items'),
    path('update_menu_items/<int:pk>/', views.update_menu_items, name='update_menu_items'),


    # View Registered Students
    path("view_students/",views.view_students,name='view_students'),
    path("edit_student/<int:student_id>/",views.edit_student,name='edit_student'),


#    Order
    path("create_order/",views.create_order,name='create_order'),
    path("add_order_item/",views.add_order_item,name='add_order_item'),
    path('complete_order/', views.complete_order, name='complete_order'),
    path('cancel_order/', views.cancel_order, name='cancel_order'),
    path('get_all_orders/', views.get_all_orders, name='get_all_orders'),
    path('get_order_by_id/<int:order_id>/', views.get_order_by_id, name='get_order_by_id'),
]



