from django.urls import path

from . import views

app_name = "quiz"

urlpatterns = [
    path("", views.dashboard_view, name="dashboard"),
    path("register/", views.register_view, name="register"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("participant-profile/", views.participant_profile_view, name="participant_profile"),
    path("quiz/<int:quiz_id>/", views.take_quiz_view, name="take_quiz"),
    path("result/<int:attempt_id>/", views.result_view, name="result"),
    path("admin-panel/", views.admin_quiz_dashboard_view, name="admin_dashboard"),
    path("admin-panel/quizzes/new/", views.admin_quiz_create_view, name="admin_quiz_create"),
    path("admin-panel/quizzes/<int:quiz_id>/edit/", views.admin_quiz_edit_view, name="admin_quiz_edit"),
    path("admin-panel/quizzes/<int:quiz_id>/", views.admin_quiz_detail_view, name="admin_quiz_detail"),
    path(
        "admin-panel/quizzes/<int:quiz_id>/toggle-publish/",
        views.admin_quiz_toggle_publish_view,
        name="admin_quiz_toggle_publish",
    ),
    path("admin-panel/quizzes/<int:quiz_id>/delete/", views.admin_quiz_delete_view, name="admin_quiz_delete"),
    path(
        "admin-panel/quizzes/<int:quiz_id>/questions/new/",
        views.admin_question_create_view,
        name="admin_question_create",
    ),
    path(
        "admin-panel/quizzes/<int:quiz_id>/questions/<int:question_id>/edit/",
        views.admin_question_edit_view,
        name="admin_question_edit",
    ),
    path(
        "admin-panel/quizzes/<int:quiz_id>/questions/<int:question_id>/delete/",
        views.admin_question_delete_view,
        name="admin_question_delete",
    ),
]
