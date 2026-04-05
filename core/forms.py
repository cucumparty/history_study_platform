"""Forms for the history learning application."""

from django import forms


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


class CardCreateForm(forms.Form):
    """Form for creating a new history flashcard."""

    ERA_CHOICES_PLACEHOLDER = [("", "— Выберите эпоху —")]

    front = forms.CharField(
        label="Лицевая сторона",
        max_length=400,
        widget=forms.TextInput(attrs={
            "class": "form-input",
            "placeholder": "Дата или вопрос — например: «1703 год»",
        }),
        error_messages={
            "required": "Введите дату или вопрос для лицевой стороны карточки.",
            "max_length": "Текст слишком длинный — не более 400 символов.",
        },
    )

    back = forms.CharField(
        label="Обратная сторона",
        widget=forms.Textarea(attrs={
            "class": "form-input form-input--textarea",
            "placeholder": "Событие или ответ",
            "rows": 3,
        }),
        error_messages={
            "required": "Введите событие или ответ для обратной стороны карточки.",
        },
    )

    hint = forms.CharField(
        label="Подсказка (необязательно)",
        max_length=300,
        required=False,
        widget=forms.TextInput(attrs={
            "class": "form-input",
            "placeholder": "Маленькая подсказка, если застряли",
        }),
        error_messages={
            "max_length": "Подсказка слишком длинная — не более 300 символов.",
        },
    )

    era = forms.ChoiceField(
        label="Эпоха",
        error_messages={
            "required": "Пожалуйста, выберите эпоху.",
            "invalid_choice": "Выбрана несуществующая эпоха.",
        },
    )

    def __init__(self, *args, era_choices=None, **kwargs):
        super().__init__(*args, **kwargs)
        choices = self.ERA_CHOICES_PLACEHOLDER + (era_choices or [])
        self.fields["era"].choices = choices

    def clean_front(self):
        """Ensure front text is not only whitespace."""
        value = self.cleaned_data.get("front", "").strip()
        if not value:
            raise forms.ValidationError(
                "Текст лицевой стороны не может состоять только из пробелов."
            )
        return value

    def clean_back(self):
        """Ensure back text is not only whitespace."""
        value = self.cleaned_data.get("back", "").strip()
        if not value:
            raise forms.ValidationError(
                "Текст обратной стороны не может состоять только из пробелов."
            )
        return value

    def clean_era(self):
        """Validate era id is a positive integer."""
        value = self.cleaned_data.get("era", "")
        if not value:
            raise forms.ValidationError("Пожалуйста, выберите эпоху.")
        try:
            era_id = int(value)
        except (ValueError, TypeError) as exc:
            raise forms.ValidationError("Некорректный идентификатор эпохи.") from exc
        if era_id <= 0:
            raise forms.ValidationError("Некорректный идентификатор эпохи.")
        return era_id


class QuizSettingsForm(forms.Form):
    """
    Form for configuring a quiz session:
    which era to draw questions from and how many questions.
    """

    COUNT_CHOICES = [
        (3,  "3 вопроса — быстрая разминка"),
        (5,  "5 вопросов — стандарт"),
        (10, "10 вопросов — серьёзная проверка"),
    ]

    era = forms.ChoiceField(
        label="Тема (эпоха)",
        required=True,
        error_messages={
            "required": "Пожалуйста, выберите эпоху.",
            "invalid_choice": "Выбрана несуществующая эпоха.",
        },
    )

    count = forms.ChoiceField(
        label="Количество вопросов",
        choices=COUNT_CHOICES,
        initial=5,
        error_messages={
            "required": "Укажите количество вопросов.",
            "invalid_choice": "Недопустимое количество вопросов.",
        },
    )

    def __init__(self, *args, era_choices=None, **kwargs):
        super().__init__(*args, **kwargs)
        base = [("all", "Все эпохи")]
        self.fields["era"].choices = base + (era_choices or [])

    def clean_count(self):
        """Ensure count is a valid positive integer."""
        raw = self.cleaned_data.get("count")
        try:
            value = int(raw)
        except (ValueError, TypeError) as exc:
            raise forms.ValidationError("Некорректное количество вопросов.") from exc
        allowed = [c[0] for c in self.COUNT_CHOICES]
        if value not in allowed:
            raise forms.ValidationError("Недопустимое количество вопросов.")
        return value

    def clean_era(self):
        """Accept 'all' or a numeric era pk."""
        value = self.cleaned_data.get("era", "")
        if value == "all":
            return "all"
        try:
            era_id = int(value)
        except (ValueError, TypeError) as exc:
            raise forms.ValidationError("Некорректный идентификатор эпохи.") from exc
        if era_id <= 0:
            raise forms.ValidationError("Некорректный идентификатор эпохи.")
        return era_id
