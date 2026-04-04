"""Views for the history learning application."""

from django.shortcuts import render, get_object_or_404
from django.http import Http404
from .models import Era, Lecture, HistoryFact
from .forms import LectureTestForm


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

    # Determine prev / next lectures for navigation
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
