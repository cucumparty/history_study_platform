"""URL configuration for the core app."""

from django.urls import path
from . import views

app_name = "core"

urlpatterns = [
    path("", views.home, name="home"),
    path("about/", views.about, name="about"),
    # Lectures
    path("lectures/", views.lecture_list, name="lecture_list"),
    path("lectures/<slug:slug>/", views.lecture_detail, name="lecture_detail"),
    path("lectures/<slug:slug>/test/", views.lecture_test, name="lecture_test"),
    # Cards
    path("cards/", views.card_list, name="card_list"),
    path("cards/train/", views.card_train, name="card_train"),
    # Quiz
    path("quiz/", views.quiz_home, name="quiz_home"),
    path("quiz/play/", views.quiz_play, name="quiz_play"),
    # Facts & Timeline
    path("facts/", views.fact_list, name="fact_list"),
    path("timeline/", views.timeline, name="timeline"),
]
