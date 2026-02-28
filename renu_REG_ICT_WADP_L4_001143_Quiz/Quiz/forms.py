from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.forms import BaseInlineFormSet, inlineformset_factory

from .models import Option, Participant, Question, Quiz

User = get_user_model()


class RegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].required = False
        self.fields["username"].help_text = ""

    def clean_email(self):
        email = self.cleaned_data["email"].lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("This email is already in use.")
        return email

    def clean_username(self):
        username = (self.cleaned_data.get("username") or "").strip()
        if username:
            if User.objects.filter(username__iexact=username).exists():
                raise forms.ValidationError("This username is already in use.")
            return username

        email = (self.cleaned_data.get("email") or "").strip().lower()
        base_username = email.split("@")[0] if "@" in email else "user"
        candidate = base_username
        counter = 1
        while User.objects.filter(username__iexact=candidate).exists():
            candidate = f"{base_username}{counter}"
            counter += 1
        return candidate


class LoginForm(AuthenticationForm):
    username = forms.CharField(label="Username or Email")

    def clean(self):
        username_or_email = self.cleaned_data.get("username")
        password = self.cleaned_data.get("password")

        if username_or_email and "@" in username_or_email:
            try:
                user = User.objects.get(email__iexact=username_or_email)
                self.cleaned_data["username"] = user.username
            except User.DoesNotExist:
                pass

        return super().clean()


class ParticipantForm(forms.ModelForm):
    class Meta:
        model = Participant
        fields = ("name", "student_class", "age", "gender", "institution")


class QuizSubmissionForm(forms.Form):
    quiz_id = forms.IntegerField(widget=forms.HiddenInput)

    def __init__(self, *args, quiz: Quiz, **kwargs):
        super().__init__(*args, **kwargs)
        self.quiz = quiz
        self.fields["quiz_id"].initial = quiz.id
        for question in quiz.questions.prefetch_related("options").all():
            choices = [(str(option.id), option.option) for option in question.options.all().order_by("?")]
            self.fields[f"question_{question.id}"] = forms.ChoiceField(
                label=question.question,
                choices=choices,
                widget=forms.RadioSelect,
            )


class QuizForm(forms.ModelForm):
    class Meta:
        model = Quiz
        fields = ("title", "description")


class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ("question",)


class BaseOptionInlineFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()
        correct_count = 0
        option_count = 0

        for form in self.forms:
            if not hasattr(form, "cleaned_data"):
                continue
            if self.can_delete and form.cleaned_data.get("DELETE"):
                continue
            if not form.cleaned_data.get("option"):
                continue
            option_count += 1
            if form.cleaned_data.get("is_correct"):
                correct_count += 1

        if option_count < 2:
            raise forms.ValidationError("At least 2 options are required.")
        if correct_count != 1:
            raise forms.ValidationError("Exactly 1 option must be marked as correct.")


OptionCreateFormSet = inlineformset_factory(
    Question,
    Option,
    fields=("option", "is_correct"),
    formset=BaseOptionInlineFormSet,
    extra=2,
    can_delete=True,
)

OptionEditFormSet = inlineformset_factory(
    Question,
    Option,
    fields=("option", "is_correct"),
    formset=BaseOptionInlineFormSet,
    extra=0,
    can_delete=True,
)
