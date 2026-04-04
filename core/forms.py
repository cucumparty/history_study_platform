"""Forms for the history learning application."""

from django import forms
from .models import HistoryCard, Era, Lecture


class LectureTestForm(forms.Form):
    """
    Dynamically built form for the post-lecture test.
    Accepts a queryset of QuizQuestion objects and creates
    a radio-select field for each question.
    """

    def __init__(self, *args, questions=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.questions = questions or []
        for question in self.questions:
            field_name = f"question_{question.pk}"
            self.fields[field_name] = forms.ChoiceField(
                label=question.text,
                choices=question.get_options(),
                widget=forms.RadioSelect(attrs={"class": "test-radio"}),
                error_messages={
                    "required": "Пожалуйста, выберите один из вариантов ответа.",
                },
            )

    def get_results(self):
        """
        Compare submitted answers with correct options.
        Returns list of dicts: {question, chosen, is_correct}.
        """
        results = []
        for question in self.questions:
            field_name = f"question_{question.pk}"
            chosen = self.cleaned_data.get(field_name, "")
            results.append(
                {
                    "question": question,
                    "chosen": chosen,
                    "is_correct": chosen == question.correct_option,
                }
            )
        return results


class CardCreateForm(forms.ModelForm):
    """Form for creating a new flashcard."""

    era = forms.ModelChoiceField(
        queryset=Era.objects.all(),
        required=False,
        empty_label="— Не привязывать к эпохе —",
        label="Эпоха",
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    lecture = forms.ModelChoiceField(
        queryset=Lecture.objects.select_related("era").order_by(
            "era__order", "order"
        ),
        required=False,
        empty_label="— Не привязывать к лекции —",
        label="Лекция",
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    class Meta:
        model = HistoryCard
        fields = ["front", "back", "hint", "era", "lecture"]
        labels = {
            "front": "Лицевая сторона",
            "back": "Обратная сторона",
            "hint": "Подсказка (необязательно)",
        }
        help_texts = {
            "front": "Дата, понятие или вопрос — то, что видно сначала.",
            "back": "Событие, определение или ответ — раскрывается при перевороте.",
            "hint": "Небольшая подсказка, если карточка слишком сложная.",
        }
        widgets = {
            "front": forms.TextInput(attrs={
                "class": "form-input",
                "placeholder": "Например: 1703 год",
            }),
            "back": forms.Textarea(attrs={
                "class": "form-textarea",
                "rows": 3,
                "placeholder": "Например: Основание Санкт-Петербурга Петром I",
            }),
            "hint": forms.TextInput(attrs={
                "class": "form-input",
                "placeholder": "Например: Связано с Петром I",
            }),
        }

    def clean_front(self):
        """Validate front side is not empty or whitespace-only."""
        value = self.cleaned_data.get("front", "").strip()
        if not value:
            raise forms.ValidationError(
                "Лицевая сторона не может быть пустой."
            )
        if len(value) < 2:
            raise forms.ValidationError(
                "Слишком короткое значение — минимум 2 символа."
            )
        return value

    def clean_back(self):
        """Validate back side is meaningful."""
        value = self.cleaned_data.get("back", "").strip()
        if not value:
            raise forms.ValidationError(
                "Обратная сторона не может быть пустой."
            )
        if len(value) < 5:
            raise forms.ValidationError(
                "Напишите немного подробнее — минимум 5 символов."
            )
        return value
