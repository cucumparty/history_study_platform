"""Models for the history learning application."""

from django.db import models


class Era(models.Model):
    """Historical era grouping topics."""

    name = models.CharField(max_length=200, verbose_name="Название эпохи")
    description = models.TextField(verbose_name="Описание", blank=True)
    order = models.PositiveIntegerField(default=0, verbose_name="Порядок")
    color = models.CharField(
        max_length=7, default="#8B4513", verbose_name="Цвет (hex)"
    )

    class Meta:
        ordering = ["order"]
        verbose_name = "Эпоха"
        verbose_name_plural = "Эпохи"

    def __str__(self):
        return str(self.name)


class Lecture(models.Model):
    """Historical lecture with content and a test at the end."""

    era = models.ForeignKey(
        Era,
        on_delete=models.CASCADE,
        related_name="lectures",
        verbose_name="Эпоха",
    )
    title = models.CharField(max_length=300, verbose_name="Заголовок")
    slug = models.SlugField(unique=True, verbose_name="URL-slug")
    short_description = models.CharField(
        max_length=500, verbose_name="Краткое описание"
    )
    content = models.TextField(verbose_name="Содержание лекции")
    year_start = models.IntegerField(
        null=True, blank=True, verbose_name="Начало периода (год)"
    )
    year_end = models.IntegerField(
        null=True, blank=True, verbose_name="Конец периода (год)"
    )
    order = models.PositiveIntegerField(default=0, verbose_name="Порядок")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["era__order", "order"]
        verbose_name = "Лекция"
        verbose_name_plural = "Лекции"

    def __str__(self):
        return str(self.title)

    def year_display(self):
        """Return human-readable year range."""
        if self.year_start and self.year_end:
            return f"{self.year_start} – {self.year_end}"
        if self.year_start:
            return str(self.year_start)
        return ""


class HistoryCard(models.Model):
    """Flashcard for memorizing dates and events."""

    lecture = models.ForeignKey(
        Lecture,
        on_delete=models.CASCADE,
        related_name="cards",
        verbose_name="Лекция",
        null=True,
        blank=True,
    )
    front = models.CharField(max_length=400, verbose_name="Лицевая сторона (дата/вопрос)")
    back = models.TextField(verbose_name="Обратная сторона (ответ/событие)")
    hint = models.CharField(
        max_length=300, blank=True, verbose_name="Подсказка"
    )
    era = models.ForeignKey(
        Era,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="cards",
        verbose_name="Эпоха",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Карточка"
        verbose_name_plural = "Карточки"

    def __str__(self):
        return str(self.front)


class QuizQuestion(models.Model):
    """A multiple-choice question for quizzes and lecture tests."""

    QUESTION_TYPE_CHOICES = [
        ("lecture_test", "Тест после лекции"),
        ("quiz", "Квиз"),
    ]

    lecture = models.ForeignKey(
        Lecture,
        on_delete=models.CASCADE,
        related_name="questions",
        verbose_name="Лекция",
        null=True,
        blank=True,
    )
    question_type = models.CharField(
        max_length=20,
        choices=QUESTION_TYPE_CHOICES,
        default="quiz",
        verbose_name="Тип вопроса",
    )
    text = models.TextField(verbose_name="Текст вопроса")
    option_a = models.CharField(max_length=300, verbose_name="Вариант А")
    option_b = models.CharField(max_length=300, verbose_name="Вариант Б")
    option_c = models.CharField(max_length=300, verbose_name="Вариант В")
    option_d = models.CharField(max_length=300, verbose_name="Вариант Г")
    correct_option = models.CharField(
        max_length=1,
        choices=[("A", "A"), ("B", "B"), ("C", "C"), ("D", "D")],
        verbose_name="Правильный вариант",
    )
    explanation = models.TextField(
        blank=True, verbose_name="Объяснение правильного ответа"
    )
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order"]
        verbose_name = "Вопрос"
        verbose_name_plural = "Вопросы"

    def __str__(self):
        return str(self.text[:80])

    def get_options(self):
        """Return list of (letter, text) tuples."""
        return [
            ("A", self.option_a),
            ("B", self.option_b),
            ("C", self.option_c),
            ("D", self.option_d),
        ]


class HistoryFact(models.Model):
    """Interesting historical fact."""

    era = models.ForeignKey(
        Era,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="facts",
        verbose_name="Эпоха",
    )
    title = models.CharField(max_length=300, verbose_name="Заголовок факта")
    content = models.TextField(verbose_name="Содержание")
    year = models.IntegerField(null=True, blank=True, verbose_name="Год события")
    is_featured = models.BooleanField(default=False, verbose_name="Показать на главной")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-is_featured", "-created_at"]
        verbose_name = "Интересный факт"
        verbose_name_plural = "Интересные факты"

    def __str__(self):
        return str(self.title)


class TimelineEvent(models.Model):
    """Event for the parallel timelines comparison feature."""

    REGION_CHOICES = [
        ("russia", "Россия"),
        ("europe", "Европа"),
        ("asia", "Азия"),
        ("america", "Америка"),
        ("middle_east", "Ближний Восток"),
        ("other", "Другое"),
    ]

    title = models.CharField(max_length=300, verbose_name="Событие")
    year = models.IntegerField(verbose_name="Год")
    region = models.CharField(
        max_length=20,
        choices=REGION_CHOICES,
        verbose_name="Регион",
    )
    description = models.TextField(blank=True, verbose_name="Описание")
    era = models.ForeignKey(
        Era,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="events",
        verbose_name="Эпоха",
    )

    class Meta:
        ordering = ["year"]
        verbose_name = "Событие на таймлайне"
        verbose_name_plural = "События на таймлайне"

    def __str__(self):
        return f"{self.year}: {self.title}"
