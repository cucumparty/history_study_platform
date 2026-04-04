"""Forms for the history learning application."""

from django import forms
from .models import QuizQuestion


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
