"""Views for the history learning application."""

import random

from django.contrib import messages
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render

from .forms import CardCreateForm, LectureTestForm, QuizSettingsForm
from .models import Era, HistoryCard, HistoryFact, Lecture, QuizQuestion


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

    if era_id:
        try:
            cards = HistoryCard.objects.filter(
                era_id=int(era_id)
            ).select_related("era", "lecture")
            active_era = Era.objects.filter(pk=int(era_id)).first()
        except (ValueError, TypeError):
            cards = HistoryCard.objects.select_related("era", "lecture").all()
            active_era = None
    else:
        cards = HistoryCard.objects.select_related("era", "lecture").all()
        active_era = None

    era_choices = [(era.pk, era.name) for era in eras]
    form = CardCreateForm(era_choices=era_choices)

    context = {
        "cards": cards,
        "eras": eras,
        "active_era": active_era,
        "era_id": era_id,
        "form": form,
        "total": HistoryCard.objects.count(),
    }
    return render(request, "core/card_list.html", context)


def card_create(request):
    """Handle POST: create a new flashcard."""
    eras = Era.objects.all()
    era_choices = [(era.pk, era.name) for era in eras]

    if request.method == "POST":
        form = CardCreateForm(request.POST, era_choices=era_choices)
        if form.is_valid():
            era_obj = get_object_or_404(Era, pk=form.cleaned_data["era"])
            HistoryCard.objects.create(
                front=form.cleaned_data["front"],
                back=form.cleaned_data["back"],
                hint=form.cleaned_data.get("hint", ""),
                era=era_obj,
            )
            messages.success(
                request,
                f"Карточка «{form.cleaned_data['front']}» успешно добавлена!"
            )
            return redirect("core:card_list")

        cards = HistoryCard.objects.select_related("era", "lecture").all()
        context = {
            "cards": cards,
            "eras": eras,
            "active_era": None,
            "era_id": "",
            "form": form,
            "total": HistoryCard.objects.count(),
            "show_form": True,
        }
        return render(request, "core/card_list.html", context)

    return redirect("core:card_list")


def card_train(request):
    """Flashcard training mode — one card at a time."""
    eras = Era.objects.all()
    era_id = request.GET.get("era", "")

    if era_id:
        try:
            cards = list(
                HistoryCard.objects.filter(
                    era_id=int(era_id)
                ).select_related("era")
            )
            active_era = Era.objects.filter(pk=int(era_id)).first()
        except (ValueError, TypeError):
            cards = list(HistoryCard.objects.select_related("era").all())
            active_era = None
    else:
        cards = list(HistoryCard.objects.select_related("era").all())
        active_era = None

    random.shuffle(cards)

    context = {
        "cards": cards,
        "cards_json": _cards_to_json(cards),
        "eras": eras,
        "active_era": active_era,
        "era_id": era_id,
        "total": len(cards),
    }
    return render(request, "core/card_train.html", context)


def _cards_to_json(cards):
    """Serialize cards to a JSON-safe list for JS."""
    import json  # noqa: PLC0415
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
    context = {
        "form": form,
        "era_stats": era_stats,
        "total_q": total_q,
    }
    return render(request, "core/quiz_home.html", context)


def quiz_play(request):
    """Active quiz session — questions one by one, result at end."""
    eras = Era.objects.all()
    era_id = request.GET.get("era", "")
    count = request.GET.get("count", "5")

    try:
        count = int(count)
        if count not in (3, 5, 10):
            count = 5
    except (ValueError, TypeError):
        count = 5

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
        results = []
        score = 0
        for question in questions:
            chosen = request.POST.get(f"q_{question.pk}", "")
            is_correct = chosen == question.correct_option
            if is_correct:
                score += 1
            results.append({
                "question": question,
                "chosen": chosen,
                "is_correct": is_correct,
                "options": question.get_options(),
            })

        q_ids = request.POST.get("question_ids", "")
        if q_ids:
            try:
                id_list = [int(x) for x in q_ids.split(",") if x.strip()]
                ordered = {q.pk: q for q in questions}
                questions = [ordered[pk] for pk in id_list if pk in ordered]
            except (ValueError, AttributeError):
                pass

        total = len(results)
        percent = int(score / total * 100) if total else 0
        context = {
            "results": results,
            "score": score,
            "total": total,
            "percent": percent,
            "era_id": era_id,
            "count": count,
            "eras": eras,
        }
        return render(request, "core/quiz_result.html", context)

    question_ids = ",".join(str(q.pk) for q in questions)
    context = {
        "questions": questions,
        "question_ids": question_ids,
        "total": len(questions),
        "era_id": era_id,
        "count": count,
        "eras": eras,
    }
    return render(request, "core/quiz_play.html", context)
