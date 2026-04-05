"""Views for the history learning application."""

import json
import random

from django.contrib import messages
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render

from .forms import LectureTestForm, QuizSettingsForm
from .models import (
    Era, HistoryCard, HistoryFact, Lecture,
    QuizQuestion, TimelineEvent,
)


# ─── HOME & ABOUT ─────────────────────────────────────────────────────────────

def home(request):
    """Main landing page."""
    eras = Era.objects.prefetch_related("lectures").all()
    featured_facts = HistoryFact.objects.filter(is_featured=True)[:3]
    total_lectures = Lecture.objects.count()
    context = {
        "eras": eras,
        "featured_facts": featured_facts,
        "total_lectures": total_lectures,
    }
    return render(request, "core/home.html", context)


def about(request):
    """About the project page."""
    return render(request, "core/about.html")


# ─── LECTURES ─────────────────────────────────────────────────────────────────

def lecture_list(request):
    """List of all lectures grouped by era."""
    eras = Era.objects.prefetch_related("lectures").all()
    total = Lecture.objects.count()
    context = {"eras": eras, "total": total}
    return render(request, "core/lecture_list.html", context)


def lecture_detail(request, slug):
    """Full text of a single lecture."""
    lecture = get_object_or_404(
        Lecture.objects.select_related("era").prefetch_related("cards"),
        slug=slug,
    )
    questions = list(
        lecture.questions.filter(question_type="lecture_test").order_by("order")
    )
    all_lectures = list(Lecture.objects.order_by("era__order", "order"))
    try:
        idx = next(i for i, lec in enumerate(all_lectures) if lec.pk == lecture.pk)
    except StopIteration:
        idx = 0
    prev_lecture = all_lectures[idx - 1] if idx > 0 else None
    next_lecture = all_lectures[idx + 1] if idx < len(all_lectures) - 1 else None
    context = {
        "lecture": lecture,
        "questions": questions,
        "has_test": bool(questions),
        "prev_lecture": prev_lecture,
        "next_lecture": next_lecture,
    }
    return render(request, "core/lecture_detail.html", context)


def lecture_test(request, slug):
    """Handle POST of the lecture test and show results."""
    lecture = get_object_or_404(Lecture, slug=slug)
    questions = list(
        lecture.questions.filter(question_type="lecture_test").order_by("order")
    )
    if not questions:
        raise Http404("У этой лекции нет теста.")
    if request.method == "POST":
        form = LectureTestForm(request.POST, questions=questions)
        if form.is_valid():
            results = form.get_results()
            score = sum(1 for r in results if r["is_correct"])
            total = len(results)
            percent = int(score / total * 100) if total else 0
            context = {
                "lecture": lecture,
                "results": results,
                "score": score,
                "total": total,
                "percent": percent,
            }
            return render(request, "core/lecture_test_result.html", context)
    else:
        form = LectureTestForm(questions=questions)
    context = {"lecture": lecture, "form": form, "questions": questions}
    return render(request, "core/lecture_test.html", context)


# ─── CARDS ────────────────────────────────────────────────────────────────────

def card_list(request):
    """Show all flashcards, filterable by era."""
    eras = Era.objects.all()
    era_id = request.GET.get("era", "")
    selected_era = None
    if era_id:
        try:
            selected_era = Era.objects.filter(pk=int(era_id)).first()
            cards = HistoryCard.objects.filter(
                era_id=int(era_id)
            ).select_related("era", "lecture")
        except (ValueError, TypeError):
            cards = HistoryCard.objects.select_related("era", "lecture").all()
    else:
        cards = HistoryCard.objects.select_related("era", "lecture").all()

    context = {
        "cards": cards,
        "eras": eras,
        "selected_era": selected_era,
    }
    return render(request, "core/card_list.html", context)


def card_train(request):
    """Flashcard training mode — one card at a time."""
    eras = Era.objects.all()
    era_id = request.GET.get("era", "")
    selected_era = None
    if era_id:
        try:
            selected_era = Era.objects.filter(pk=int(era_id)).first()
            cards = list(
                HistoryCard.objects.filter(
                    era_id=int(era_id)
                ).select_related("era")
            )
        except (ValueError, TypeError):
            cards = list(HistoryCard.objects.select_related("era").all())
    else:
        cards = list(HistoryCard.objects.select_related("era").all())

    random.shuffle(cards)
    context = {
        "cards": cards,
        "cards_json": _cards_to_json(cards),
        "eras": eras,
        "selected_era": selected_era,
        "total": len(cards),
    }
    return render(request, "core/card_train.html", context)


def _cards_to_json(cards):
    """Serialize cards to a JSON-safe list for JS."""
    data = [
        {
            "id": c.pk,
            "front": c.front,
            "back": c.back,
            "hint": c.hint,
            "era": c.era.name if c.era else "",
        }
        for c in cards
    ]
    return json.dumps(data, ensure_ascii=False)


# ─── QUIZ ─────────────────────────────────────────────────────────────────────

def quiz_home(request):
    """Quiz start page — choose era and question count."""
    eras = Era.objects.all()
    era_choices = [(era.pk, era.name) for era in eras]
    if request.method == "POST":
        form = QuizSettingsForm(request.POST, era_choices=era_choices)
        if form.is_valid():
            era_val = form.cleaned_data["era"]
            count = form.cleaned_data["count"]
            url = f"/quiz/play/?count={count}"
            if era_val != "all":
                url += f"&era={era_val}"
            return redirect(url)
    else:
        form = QuizSettingsForm(era_choices=era_choices)
    era_stats = []
    for era in eras:
        q_count = QuizQuestion.objects.filter(lecture__era=era).count()
        era_stats.append({"era": era, "q_count": q_count})
    total_q = QuizQuestion.objects.count()
    context = {"form": form, "era_stats": era_stats, "total_q": total_q}
    return render(request, "core/quiz_home.html", context)


def quiz_play(request):
    """Active quiz session — questions one by one, result at end."""
    eras = Era.objects.all()
    era_id = request.GET.get("era", "")
    count = _parse_quiz_count(request.GET.get("count", "5"))
    qs_filter = QuizQuestion.objects.select_related("lecture__era")
    if era_id:
        try:
            qs_filter = qs_filter.filter(lecture__era_id=int(era_id))
        except (ValueError, TypeError):
            pass
    pool = list(qs_filter)
    if not pool:
        messages.error(
            request,
            "По выбранной теме нет вопросов. Попробуйте другую эпоху."
        )
        return redirect("core:quiz_home")
    random.shuffle(pool)
    questions = pool[:count]
    if request.method == "POST":
        results, score = _grade_quiz(request.POST, questions)
        total = len(results)
        percent = int(score / total * 100) if total else 0
        context = {
            "results": results, "score": score, "total": total,
            "percent": percent, "era_id": era_id, "count": count, "eras": eras,
        }
        return render(request, "core/quiz_result.html", context)
    question_ids = ",".join(str(q.pk) for q in questions)
    context = {
        "questions": questions, "question_ids": question_ids,
        "total": len(questions), "era_id": era_id,
        "count": count, "eras": eras,
    }
    return render(request, "core/quiz_play.html", context)


def _parse_quiz_count(raw):
    """Return a valid question count (3, 5, or 10)."""
    try:
        value = int(raw)
        return value if value in (3, 5, 10) else 5
    except (ValueError, TypeError):
        return 5


def _grade_quiz(post_data, questions):
    """Score submitted quiz answers. Returns (results list, score int)."""
    results = []
    score = 0
    for question in questions:
        chosen = post_data.get(f"q_{question.pk}", "")
        is_correct = chosen == question.correct_option
        if is_correct:
            score += 1
        results.append({
            "question": question,
            "chosen": chosen,
            "is_correct": is_correct,
            "options": question.get_options(),
        })
    return results, score


# ─── FACTS ────────────────────────────────────────────────────────────────────

def fact_list(request):
    """Page with all interesting historical facts, filterable by era."""
    eras = Era.objects.all()
    era_id = request.GET.get("era", "")
    selected_era = None
    if era_id:
        try:
            selected_era = Era.objects.filter(pk=int(era_id)).first()
            facts = HistoryFact.objects.filter(
                era_id=int(era_id)
            ).select_related("era").order_by("-is_featured", "year")
        except (ValueError, TypeError):
            facts = HistoryFact.objects.select_related("era").order_by(
                "-is_featured", "year"
            )
    else:
        facts = HistoryFact.objects.select_related("era").order_by(
            "-is_featured", "year"
        )
    context = {
        "facts": facts,
        "eras": eras,
        "selected_era": selected_era,
        "total": HistoryFact.objects.count(),
    }
    return render(request, "core/fact_list.html", context)


# ─── TIMELINE ─────────────────────────────────────────────────────────────────

def timeline(request):
    """Parallel timeline: Russia on the left, the world on the right."""
    eras = Era.objects.all()
    era_id = request.GET.get("era", "")
    selected_era = None

    events_qs = TimelineEvent.objects.select_related("era").order_by("year")
    if era_id:
        try:
            selected_era = Era.objects.filter(pk=int(era_id)).first()
            events_qs = events_qs.filter(era_id=int(era_id))
        except (ValueError, TypeError):
            pass

    all_events = list(events_qs)
    russia_events = [e for e in all_events if e.region == "russia"]
    world_events = [e for e in all_events if e.region != "russia"]

    all_years = sorted({e.year for e in all_events})
    year_groups = []
    for year in all_years:
        rus = [e for e in russia_events if e.year == year]
        wld = [e for e in world_events if e.year == year]
        if rus or wld:
            year_groups.append({"year": year, "russia": rus, "world": wld})

    region_labels = dict(TimelineEvent.REGION_CHOICES)
    era_presets = _build_era_presets()

    context = {
        "eras": eras,
        "selected_era": selected_era,
        "era_id": era_id,
        "year_groups": year_groups,
        "russia_count": len(russia_events),
        "world_count": len(world_events),
        "total_years": len(all_years),
        "region_labels": region_labels,
        "era_presets": era_presets,
    }
    return render(request, "core/timeline.html", context)


def _build_era_presets():
    """Return era preset list for the timeline page."""
    names = [
        ("Древняя Русь",      "Древняя Русь"),
        ("Моск. царство",     "Московское царство"),
        ("Романовы",          "Романовы: начало"),
        ("Рос. империя",      "Российская империя"),
        ("XX век",            "XX век"),
    ]
    presets = []
    for label, era_name in names:
        pk = Era.objects.filter(
            name=era_name
        ).values_list("pk", flat=True).first()
        presets.append({"label": label, "pk": pk})
    return presets
