from django.contrib import admin

from .models import Option, Participant, Question, Quiz, QuizAttempt


class OptionInline(admin.TabularInline):
    model = Option
    extra = 1


class QuestionAdmin(admin.ModelAdmin):
    inlines = [OptionInline]
    list_display = ("id", "quiz", "question")
    list_filter = ("quiz",)
    search_fields = ("question",)


class QuestionInline(admin.TabularInline):
    model = Question
    extra = 1


class QuizAdmin(admin.ModelAdmin):
    list_display = ("id", "title")
    search_fields = ("title",)
    inlines = [QuestionInline]


class ParticipantAdmin(admin.ModelAdmin):
    list_display = ("name", "student_class", "institution", "user")
    search_fields = ("name", "institution", "user__username", "user__email")


class QuizAttemptAdmin(admin.ModelAdmin):
    list_display = ("participant", "quiz", "score", "total", "created_at")
    list_filter = ("quiz",)


admin.site.register(Quiz, QuizAdmin)
admin.site.register(Question, QuestionAdmin)
admin.site.register(Participant, ParticipantAdmin)
admin.site.register(QuizAttempt, QuizAttemptAdmin)
