# Analiza Zmian w Projektach IT (Q1 i Q2 2025)

## Opis Projektu

To interaktywna aplikacja webowa zbudowana w Pythonie przy użyciu biblioteki [Dash](https://dash.plotly.com/), stworzona w celu wizualizacji i analizy zmian wprowadzonych w projektach IT w pierwszym (Q1) i drugim (Q2) kwartale 2025 roku. Aplikacja pozwala na szybki przegląd kluczowych wskaźników wydajności (KPI) oraz szczegółową analizę zadań z podziałem na platformy i typy.

## Funkcjonalności

* **Liczniki KPI:** Wyświetla kluczowe wskaźniki, takie jak całkowita liczba zakończonych zadań w Q1, Q2 oraz ogółem.
* **Filtrowanie Danych:**
    * **Filtr Kwartału:** Pozwala użytkownikowi wybrać, czy chce wyświetlić dane dla Q1 2025, Q2 2025, czy też zagregowane dane dla całego roku 2025.
    * **Filtr Platformy:** Umożliwia filtrowanie zadań według konkretnych platform (UMPIRE, WICKET, STRIDE, Ogólne/Cross-platformowe).
* **Wykres Słupkowy (2D):** Przedstawia liczbę zakończonych zadań na poszczególnych platformach w wybranym kwartale/kwartałach.
* **Wykres Słupkowy Skumulowany (Stacked Bar Chart):** Pokazuje rozkład typów zadań (np. Story, Bug, Service Request) w obrębie każdego kwartału, dając wgląd w charakter wykonywanych prac.
* **Szczegóły Zadań:** Po kliknięciu na słupek na wykresie platform, wyświetlane są szczegółowe informacje o zadaniach należących do danej platformy i kwartału.

## Instalacja i Uruchomienie

Aby uruchomić aplikację lokalnie, wykonaj następujące kroki:

### 1. Wymagania Wstępne

Upewnij się, że masz zainstalowanego Pythona (zalecana wersja 3.7+).

### 2. Klonowanie Repozytorium (lub pobranie plików)

```bash
git clone <URL_DO_TWOJEGO_REPOZYTORIUM>
cd <NAZWA_TWOJEGO_REPOZYTORIUM>