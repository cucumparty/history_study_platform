"""Admin configuration for the history app."""

from django.contrib import admin
from .models import Era, Lecture, HistoryCard, QuizQuestion, HistoryFact, TimelineEvent


@admin.register(Era)
class EraAdmin(admin.ModelAdmin):
    """Admin for historical eras."""

    list_display = ["name", "order", "color"]
    ordering = ["order"]


class QuizQuestionInline(admin.TabularInline):
    """Inline questions inside lecture admin."""

    model = QuizQuestion
    extra = 1
    fields = ["text", "option_a", "option_b", "option_c", "option_d", "correct_option", "order"]


class HistoryCardInline(admin.TabularInline):
    """Inline cards inside lecture admin."""

    model = HistoryCard
    extra = 1
    fields = ["front", "back", "hint"]


@admin.register(Lecture)
class LectureAdmin(admin.ModelAdmin):
    """Admin for lectures."""

    list_display = ["title", "era", "year_start", "year_end", "order"]
    list_filter = ["era"]
    prepopulated_fields = {"slug": ("title",)}
    inlines = [HistoryCardInline, QuizQuestionInline]


@admin.register(HistoryCard)
class HistoryCardAdmin(admin.ModelAdmin):
    """Admin for history cards."""

    list_display = ["front", "era", "lecture", "created_at"]
    list_filter = ["era"]


@admin.register(QuizQuestion)
class QuizQuestionAdmin(admin.ModelAdmin):
    """Admin for quiz questions."""

    list_display = ["text", "lecture", "question_type", "correct_option"]
    list_filter = ["question_type", "lecture__era"]


@admin.register(HistoryFact)
class HistoryFactAdmin(admin.ModelAdmin):
    """Admin for interesting facts."""

    list_display = ["title", "era", "year", "is_featured"]
    list_filter = ["era", "is_featured"]


@admin.register(TimelineEvent)
class TimelineEventAdmin(admin.ModelAdmin):
    """Admin for timeline events."""

    list_display = ["title", "year", "region", "era"]
    list_filter = ["region", "era"]
    ordering = ["year"]
