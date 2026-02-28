from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.db.models import F, Window
from django.db.models.functions import Rank
from django.http import Http404, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import never_cache

from .forms import (
    LoginForm,
    OptionCreateFormSet,
    OptionEditFormSet,
    ParticipantForm,
    QuestionForm,
    QuizForm,
    QuizSubmissionForm,
    RegistrationForm,
)
from .models import Question, Quiz, QuizAttempt


@never_cache
def register_view(request):
    if request.user.is_authenticated:
        return redirect("quiz:dashboard")

    form = RegistrationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, "Registration successful. Please complete your participant profile.")
        return redirect("quiz:participant_profile")

    return render(request, "quiz/register.html", {"form": form})


@never_cache
def login_view(request):
    if request.user.is_authenticated:
        return redirect("quiz:dashboard")

    form = LoginForm(request, data=request.POST or None)
    if request.method == "POST" and form.is_valid():
        login(request, form.get_user())
        return redirect("quiz:dashboard")

    return render(request, "quiz/login.html", {"form": form})


def logout_view(request):
    logout(request)
    return redirect("quiz:login")


@login_required
@never_cache
def participant_profile_view(request):
    participant = getattr(request.user, "participant", None)
    form = ParticipantForm(request.POST or None, instance=participant)

    if request.method == "POST" and form.is_valid():
        participant = form.save(commit=False)
        participant.user = request.user
        participant.save()
        messages.success(request, "Participant profile saved.")
        return redirect("quiz:dashboard")

    return render(request, "quiz/participant_profile.html", {"form": form})


@login_required
@never_cache
def dashboard_view(request):
    if request.user.is_staff:
        messages.info(request, "Admins cannot participate in quizzes. Use Admin Panel to manage quizzes.")
        return redirect("quiz:admin_dashboard")

    if not hasattr(request.user, "participant"):
        return redirect("quiz:participant_profile")

    quizzes = Quiz.objects.filter(is_published=True)
    attempts = QuizAttempt.objects.filter(participant=request.user.participant).select_related("quiz")
    return render(request, "quiz/dashboard.html", {"quizzes": quizzes, "attempts": attempts})


@login_required
@never_cache
def take_quiz_view(request, quiz_id):
    if request.user.is_staff:
        messages.error(request, "Admins are not allowed to participate in quizzes.")
        return redirect("quiz:admin_dashboard")

    if not hasattr(request.user, "participant"):
        return redirect("quiz:participant_profile")

    quiz = get_object_or_404(Quiz.objects.prefetch_related("questions__options"), id=quiz_id, is_published=True)
    questions = list(quiz.questions.all().order_by("?"))
    if not questions:
        raise Http404("No questions found for this quiz.")

    if request.method == "POST":
        form = QuizSubmissionForm(request.POST, quiz=quiz)
        if form.is_valid():
            score = 0
            for question in quiz.questions.all():
                selected_option_id = form.cleaned_data.get(f"question_{question.id}")
                if selected_option_id and question.options.filter(id=selected_option_id, is_correct=True).exists():
                    score += 1

            attempt = QuizAttempt.objects.create(
                participant=request.user.participant,
                quiz=quiz,
                score=score,
                total=quiz.questions.count(),
            )
            return redirect("quiz:result", attempt_id=attempt.id)
    else:
        form = QuizSubmissionForm(quiz=quiz)

    question_forms = []
    for question in questions:
        field = form[f"question_{question.id}"]
        question_forms.append((question, field))

    return render(
        request,
        "quiz/take_quiz.html",
        {
            "quiz": quiz,
            "form": form,
            "question_forms": question_forms,
        },
    )


@login_required
def result_view(request, attempt_id):
    if not hasattr(request.user, "participant"):
        return redirect("quiz:participant_profile")

    attempt = (
        QuizAttempt.objects.select_related("quiz", "participant")
        .filter(id=attempt_id, participant=request.user.participant)
        .first()
    )
    if attempt is None:
        messages.error(request, "Result not found for your account.")
        return redirect("quiz:dashboard")

    ranked_attempts = (
        QuizAttempt.objects.filter(quiz=attempt.quiz)
        .annotate(rank=Window(expression=Rank(), order_by=[F("score").desc(), F("created_at").asc()]))
    )
    ranking_row = ranked_attempts.filter(id=attempt.id).values("rank").first()
    position = ranking_row["rank"] if ranking_row else None

    leaderboard = ranked_attempts.select_related("participant")[:10]

    return render(
        request,
        "quiz/result.html",
        {
            "attempt": attempt,
            "position": position,
            "leaderboard": leaderboard,
        },
    )


def _require_staff(request):
    if not request.user.is_authenticated:
        return redirect("quiz:login")
    if not request.user.is_staff:
        messages.error(request, "Admin access required.")
        return redirect("quiz:dashboard")
    return None


@never_cache
def admin_quiz_dashboard_view(request):
    blocked = _require_staff(request)
    if blocked:
        return blocked

    quizzes = Quiz.objects.all().prefetch_related("questions")
    return render(request, "quiz/admin_dashboard.html", {"quizzes": quizzes})


@never_cache
def admin_quiz_create_view(request):
    blocked = _require_staff(request)
    if blocked:
        return blocked

    form = QuizForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        quiz = form.save()
        messages.success(request, "Quiz created successfully. Now add questions.")
        return redirect("quiz:admin_quiz_detail", quiz_id=quiz.id)

    return render(request, "quiz/admin_quiz_form.html", {"form": form})


@never_cache
def admin_quiz_edit_view(request, quiz_id):
    blocked = _require_staff(request)
    if blocked:
        return blocked

    quiz = get_object_or_404(Quiz, id=quiz_id)
    form = QuizForm(request.POST or None, instance=quiz)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Quiz updated successfully.")
        return redirect("quiz:admin_quiz_detail", quiz_id=quiz.id)

    return render(request, "quiz/admin_quiz_form.html", {"form": form, "quiz": quiz})


@never_cache
def admin_quiz_detail_view(request, quiz_id):
    blocked = _require_staff(request)
    if blocked:
        return blocked

    quiz = get_object_or_404(Quiz.objects.prefetch_related("questions__options"), id=quiz_id)
    return render(request, "quiz/admin_quiz_detail.html", {"quiz": quiz})


@never_cache
def admin_question_create_view(request, quiz_id):
    blocked = _require_staff(request)
    if blocked:
        return blocked

    quiz = get_object_or_404(Quiz, id=quiz_id)
    question_form = QuestionForm(request.POST or None)
    option_formset = OptionCreateFormSet(request.POST or None, prefix="options")

    if request.method == "POST" and question_form.is_valid() and option_formset.is_valid():
        question = question_form.save(commit=False)
        question.quiz = quiz
        question.save()

        option_formset.instance = question
        option_formset.save()

        messages.success(request, "Question and options added.")
        return redirect("quiz:admin_quiz_detail", quiz_id=quiz.id)

    return render(
        request,
        "quiz/admin_question_form.html",
        {"quiz": quiz, "question_form": question_form, "option_formset": option_formset},
    )


def admin_quiz_toggle_publish_view(request, quiz_id):
    blocked = _require_staff(request)
    if blocked:
        return blocked
    if request.method != "POST":
        return HttpResponseForbidden("Invalid request method.")

    quiz = get_object_or_404(Quiz, id=quiz_id)
    quiz.is_published = not quiz.is_published
    quiz.save(update_fields=["is_published"])
    state = "published" if quiz.is_published else "unpublished"
    messages.success(request, f"Quiz {state} successfully.")
    return redirect("quiz:admin_quiz_detail", quiz_id=quiz.id)


def admin_quiz_delete_view(request, quiz_id):
    blocked = _require_staff(request)
    if blocked:
        return blocked
    if request.method != "POST":
        return HttpResponseForbidden("Invalid request method.")

    quiz = get_object_or_404(Quiz, id=quiz_id)
    quiz.delete()
    messages.success(request, "Quiz deleted successfully.")
    return redirect("quiz:admin_dashboard")


@never_cache
def admin_question_edit_view(request, quiz_id, question_id):
    blocked = _require_staff(request)
    if blocked:
        return blocked

    quiz = get_object_or_404(Quiz, id=quiz_id)
    question = get_object_or_404(Question, id=question_id, quiz=quiz)
    question_form = QuestionForm(request.POST or None, instance=question)
    option_formset = OptionEditFormSet(request.POST or None, instance=question, prefix="options")

    if request.method == "POST" and question_form.is_valid() and option_formset.is_valid():
        question_form.save()
        option_formset.save()
        messages.success(request, "Question updated successfully.")
        return redirect("quiz:admin_quiz_detail", quiz_id=quiz.id)

    return render(
        request,
        "quiz/admin_question_form.html",
        {"quiz": quiz, "question_form": question_form, "option_formset": option_formset, "question": question},
    )


def admin_question_delete_view(request, quiz_id, question_id):
    blocked = _require_staff(request)
    if blocked:
        return blocked
    if request.method != "POST":
        return HttpResponseForbidden("Invalid request method.")

    quiz = get_object_or_404(Quiz, id=quiz_id)
    question = get_object_or_404(Question, id=question_id, quiz=quiz)
    question.delete()
    messages.success(request, "Question deleted successfully.")
    return redirect("quiz:admin_quiz_detail", quiz_id=quiz.id)
