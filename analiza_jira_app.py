import pandas as pd
import plotly.express as px
import plotly.graph_objects as go 
from dash import Dash, html, dcc, Input, Output # type: ignore
import os

# --- 1. Funkcje do parsowania i kategoryzacji danych ---

def categorize_and_filter_changes(df_raw_input, selected_quarter=None, selected_platform=None):
    """
    Kategoryzuje i filtruje zakończone zadania dla Q1 i Q2 2025
    oraz dla wybranych kwartałów/platform.
    """
    
    df = df_raw_input.copy()

    df['Due date'] = pd.to_datetime(df['Due date'], errors='coerce', format='%Y/%m/%d')
    df['Inferred due date'] = pd.to_datetime(df['Inferred due date'], errors='coerce', format='%Y/%m/%d')
    df['Completion_Date'] = df['Due date'].fillna(df['Inferred due date'])

    df_done = df[df['Status'] == 'Done'].copy()

    q1_start = pd.Timestamp('2025-01-01')
    q1_end = pd.Timestamp('2025-03-31')
    q2_start = pd.Timestamp('2025-04-01')
    q2_end = pd.Timestamp('2025-06-30')

    all_platforms_for_display = ["UMPIRE", "WICKET", "STRIDE", "Ogólne/Cross-platformowe"]

    # Nowe, wyczyszczone struktury dla danych
    categorized_data = {
        "Platforma": all_platforms_for_display,
        "Q1 2025": [0] * len(all_platforms_for_display), 
        "Q2 2025": [0] * len(all_platforms_for_display),
        "Details Q1 2025": {p: [] for p in all_platforms_for_display},
        "Details Q2 2025": {p: [] for p in all_platforms_for_display}
    }

    issue_type_breakdown = {
        'Q1 2025': {},
        'Q2 2025': {}
    }

    df['Key'] = df['Key'].astype(str)
    df_temp_for_epic = df.copy()
    df_temp_for_epic['Parent'] = df_temp_for_epic['Parent'].astype(str)
    epic_summaries = df_temp_for_epic.set_index('Key')['Summary'].astype(str).to_dict()

    # Manualne mapowania kluczy zadań do przypisanych platform i kwartałów
    # Te mapowania powinny być tworzone raz i używane do kategoryzacji
    # Zmieniono strukturę, aby klucz mapował na (kwartał, lista_kategorii)
    all_manual_overrides = {}

    # Q1 specific keys and their primary/secondary categories
    q1_specific_keys_mapping = {
        "TPD-474": ["UMPIRE", "STRIDE"], 
        "TPD-535": ["UMPIRE"], "TPD-375": ["UMPIRE"], "TPD-376": ["UMPIRE"], "TPD-252": ["UMPIRE"], 
        "TPD-333": ["WICKET"], "TPD-331": ["WICKET"], "TPD-332": ["WICKET"], "TPD-178": ["WICKET"], 
        "TPD-516": ["WICKET"], "TPD-517": ["WICKET"], "TPD-530": ["WICKET"], 
        "TPD-240": ["STRIDE"], "TPD-263": ["STRIDE"],
        # Przykłady z Q1, które były wcześniej "Ogólne", ale chcemy je tu śledzić by nie pomijać w filtrowaniu kwartału
        "TPD-158": ["Ogólne/Cross-platformowe"], # Epic CDN
        "TPD-452": ["Ogólne/Cross-platformowe"], # Epic OTT/Quiz
        "TPD-448": ["Ogólne/Cross-platformowe"], # Epic Analityka GA
        "TPD-451": ["Ogólne/Cross-platformowe"], # Epic Mobile bugs
        "TPD-330": ["Ogólne/Cross-platformowe"], # Epic QF Paweł (ale jego subtaski są Wicket)
        "TPD-200": ["Ogólne/Cross-platformowe"], # Epic Predictor Game
    }

    # Q2 specific keys and their primary/secondary categories
    q2_specific_keys_mapping = {
        "TPD-440": ["WICKET"], "TPD-442": ["WICKET"], "TPD-443": ["WICKET"], "TPD-447": ["WICKET"],
        "TPD-444": ["WICKET"], "TPD-441": ["WICKET"], "TPD-445": ["WICKET"],
        "TPD-687": ["WICKET"], "TPD-700": ["WICKET"], "TPD-763": ["WICKET"],
        "TPD-453": ["STRIDE"],
        # Przykłady z Q2, które były wcześniej "Ogólne"
        "TPD-439": ["Ogólne/Cross-platformowe"], # Epic Stride Support Improvements
        "TPD-631": ["Ogólne/Cross-platformowe"], # Epic Support
        "TPD-731": ["Ogólne/Cross-platformowe"], # Epic Bugs and Improvements
        "TPD-851": ["Ogólne/Cross-platformowe"], # Epic Scalenie środowisk
        "TPD-880": ["Ogólne/Cross-platformowe"], # Epic BRNDS ads
    }

    # Budujemy all_manual_overrides dla szybkiego dostępu
    for k, v in q1_specific_keys_mapping.items():
        all_manual_overrides[k] = {'quarter': 'Q1 2025', 'categories': v}
    for k, v in q2_specific_keys_mapping.items():
        all_manual_overrides[k] = {'quarter': 'Q2 2025', 'categories': v}


    # Iterujemy po WSZYSTKICH zakończonych zadaniach z oryginalnego df_done
    # Filtrowanie platform i kwartałów odbywa się wewnątrz pętli
    for index, row in df_done.iterrows(): 
        summary = str(row['Summary']) if pd.notna(row['Summary']) else ''
        issue_type = str(row['Issue Type']) if pd.notna(row['Issue Type']) else ''
        key = str(row['Key']) if pd.notna(row['Key']) else ''
        
        parent_key = str(row['Parent']) if pd.notna(row['Parent']) else None
        parent_summary = epic_summaries.get(parent_key, '') if parent_key else ''
        
        item_detail = f"[{key}] {summary} ({issue_type})"

        # 1. Określenie kwartału (najpierw z daty, potem z manualnych nadpisań)
        current_item_quarter_str = None
        if pd.notna(row['Completion_Date']):
            if q1_start <= row['Completion_Date'] <= q1_end:
                current_item_quarter_str = 'Q1 2025'
            elif q2_start <= row['Completion_Date'] <= q2_end:
                current_item_quarter_str = 'Q2 2025'
        
        # 2. Określenie kategorii (najpierw z manualnych nadpisań, potem z keywords)
        item_categories = [] # Lista kategorii, do których należy to zadanie

        if key in all_manual_overrides:
            # Jeśli klucz jest w manualnych nadpisaniach, użyj zdefiniowanych tam kategorii i kwartału
            item_categories = all_manual_overrides[key]['categories']
            current_item_quarter_str = all_manual_overrides[key]['quarter'] # Nadpisz kwartał z manualnego override
        else:
            # Jeśli nie ma manualnego nadpisania, użyj logiki słów kluczowych
            determined_category = "Ogólne/Cross-platformowe" # Domyślna
            if "Umpire" in summary or "Umpire" in parent_summary or "[Umpire" in summary:
                determined_category = "UMPIRE"
            elif "Wicket" in summary or "Wicket" in parent_summary or "[Wicket" in summary:
                determined_category = "WICKET"
            elif "Stride" in summary or "Stride" in parent_summary or "[Stride" in summary:
                determined_category = "STRIDE"
            item_categories.append(determined_category)


        # --- Główne filtrowanie i zliczanie ---
        # Sprawdzamy, czy zadanie pasuje do filtra kwartału
        quarter_match = (selected_quarter is None or selected_quarter == 'All 2025' or selected_quarter == current_item_quarter_str)

        if quarter_match and current_item_quarter_str:
            for cat in item_categories:
                # Sprawdzamy, czy zadanie pasuje do filtra platformy
                platform_match = (selected_platform is None or selected_platform == 'All Platforms' or selected_platform == cat)
                
                if platform_match:
                    details_key_q = f"Details {current_item_quarter_str}"
                    if cat in categorized_data[details_key_q]: # Upewnij się, że kategoria istnieje
                        categorized_data[details_key_q][cat].append(item_detail)
                        
                        # Zliczanie dla issue_type_breakdown (dotyczy tylko wybranego kwartału)
                        if current_item_quarter_str in issue_type_breakdown:
                            issue_type_breakdown[current_item_quarter_str][issue_type] = issue_type_breakdown[current_item_quarter_str].get(issue_type, 0) + 1
        
    # Finalne przeliczenie unikalnych zadań na podstawie szczegółowych list (dla głównego wykresu)
    for platform in categorized_data["Platforma"]:
        # Używamy set() dla usunięcia duplikatów
        q1_unique_items = set(categorized_data["Details Q1 2025"][platform])
        q2_unique_items = set(categorized_data["Details Q2 2025"][platform])
        
        categorized_data["Q1 2025"][categorized_data["Platforma"].index(platform)] = len(q1_unique_items)
        categorized_data["Q2 2025"][categorized_data["Platforma"].index(platform)] = len(q2_unique_items)

    return categorized_data, issue_type_breakdown 

# --- 2. Wczytanie danych z pliku CSV (tylko raz na starcie aplikacji) ---
csv_file_name = 'products_development_2025-06-19_11.34am.csv'
script_dir = os.path.dirname(__file__) 
csv_file_path = os.path.join(script_dir, csv_file_name) 

try:
    df_raw_global = pd.read_csv(csv_file_path, sep=',', quotechar='"')
    # Początkowe wczytanie danych bez filtrowania, dla inicjalizacji
    # Callbacki będą wywoływać analyze_and_filter_data z odpowiednimi filtrami
except FileNotFoundError:
    print(f"Błąd: Plik '{csv_file_name}' nie został znaleziony w katalogu '{script_dir}'.")
    print("Upewnij się, że plik CSV jest w tym samym folderze co skrypt Pythona.")
    exit()
except Exception as e:
    print(f"Wystąpił nieoczekiwany błąd podczas przetwarzania pliku CSV: {e}")
    exit()

# --- 3. Budowa aplikacji Dash z ulepszonym wyglądem i nowymi filtrami/KPI ---
app = Dash(__name__)

app.layout = html.Div(style={
    'fontFamily': 'Arial, sans-serif',
    'backgroundColor': '#f0f2f5', 
    'padding': '40px 20px',
    'minHeight': '100vh',
    'display': 'flex',
    'flexDirection': 'column',
    'alignItems': 'center'
}, children=[
    html.H1(children='Analiza Zmian w Projektach IT', style={
        'textAlign': 'center',
        'color': '#2c3e50', 
        'marginBottom': '10px',
        'fontSize': '2.8em',
        'fontWeight': 'bold'
    }),

    html.H2(children='Raport za I i II Kwartał 2025 Roku', style={
        'textAlign': 'center',
        'color': '#34495e',
        'marginBottom': '40px',
        'fontSize': '1.8em',
        'fontWeight': 'normal'
    }),

    # --- KPI Section ---
    html.Div(style={
        'display': 'flex',
        'justifyContent': 'space-around',
        'width': '100%',
        'maxWidth': '1000px',
        'marginBottom': '40px',
        'flexWrap': 'wrap',
        'gap': '20px'
    }, children=[
        html.Div(style=
            {
                'backgroundColor': '#ffffff',
                'borderRadius': '12px',
                'boxShadow': '0 2px 10px rgba(0, 0, 0, 0.05)',
                'padding': '20px',
                'textAlign': 'center',
                'flex': '1',
                'minWidth': '200px'
            }, children=[
            html.H3("Zadania zakończone w Q1", style={'color': '#2ecc71', 'fontSize': '1.2em', 'marginBottom': '10px'}),
            html.P(id='kpi-q1-total', style={'fontSize': '2em', 'fontWeight': 'bold', 'color': '#34495e'})
        ]),
        html.Div(style=
            {
                'backgroundColor': '#ffffff',
                'borderRadius': '12px',
                'boxShadow': '0 2px 10px rgba(0, 0, 0, 0.05)',
                'padding': '20px',
                'textAlign': 'center',
                'flex': '1',
                'minWidth': '200px'
            }, children=[
            html.H3("Zadania zakończone w Q2", style={'color': '#3498db', 'fontSize': '1.2em', 'marginBottom': '10px'}),
            html.P(id='kpi-q2-total', style={'fontSize': '2em', 'fontWeight': 'bold', 'color': '#34495e'})
        ]),
        html.Div(style=
            {
                'backgroundColor': '#ffffff',
                'borderRadius': '12px',
                'boxShadow': '0 2px 10px rgba(0, 0, 0, 0.05)',
                'padding': '20px',
                'textAlign': 'center',
                'flex': '1',
                'minWidth': '200px'
            }, children=[
            html.H3("Zadania zakończone ogółem", style={'color': '#8e44ad', 'fontSize': '1.2em', 'marginBottom': '10px'}),
            html.P(id='kpi-total-overall', style={'fontSize': '2em', 'fontWeight': 'bold', 'color': '#34495e'})
        ])
    ]),

    # --- Filters Section ---
    html.Div(style={
        'backgroundColor': '#ffffff',
        'borderRadius': '12px',
        'boxShadow': '0 2px 10px rgba(0, 0, 0, 0.05)',
        'padding': '20px',
        'width': '100%',
        'maxWidth': '1000px',
        'marginBottom': '40px',
        'display': 'flex',
        'justifyContent': 'space-around',
        'flexWrap': 'wrap',
        'gap': '20px'
    }, children=[
        html.Div(style={'flex': '1', 'minWidth': '250px'}, children=[
            html.Label("Wybierz kwartał:", style={'display': 'block', 'marginBottom': '5px', 'fontWeight': 'bold', 'color': '#555'}),
            dcc.Dropdown(
                id='quarter-filter',
                options=[
                    {'label': 'Wszystkie Kwartały', 'value': 'All 2025'},
                    {'label': 'Q1 2025', 'value': 'Q1 2025'},
                    {'label': 'Q2 2025', 'value': 'Q2 2025'}
                ],
                value='All 2025', # Domyślna wartość
                clearable=False,
                style={'borderRadius': '8px', 'borderColor': '#ccc'}
            )
        ]),
        html.Div(style={'flex': '1', 'minWidth': '250px'}, children=[
            html.Label("Wybierz platformę:", style={'display': 'block', 'marginBottom': '5px', 'fontWeight': 'bold', 'color': '#555'}),
            dcc.Dropdown(
                id='platform-filter',
                options=[
                    {'label': 'Wszystkie Platformy', 'value': 'All Platforms'},
                    {'label': 'UMPIRE', 'value': 'UMPIRE'},
                    {'label': 'WICKET', 'value': 'WICKET'},
                    {'label': 'STRIDE', 'value': 'STRIDE'},
                    {'label': 'Ogólne/Cross-platformowe', 'value': 'Ogólne/Cross-platformowe'}
                ],
                value='All Platforms', # Domyślna wartość
                clearable=False,
                style={'borderRadius': '8px', 'borderColor': '#ccc'}
            )
        ])
    ]),

    # Kontener dla wykresu 2D (Liczba zadań per Platforma)
    html.Div(style={
        'backgroundColor': '#ffffff',
        'borderRadius': '12px',
        'boxShadow': '0 4px 20px rgba(0, 0, 0, 0.08)',
        'padding': '30px',
        'width': '100%',
        'maxWidth': '1000px',
        'marginBottom': '40px'
    }, children=[
        html.H3(children='Liczba Zakończonych Zadań według Platform', style={
            'textAlign': 'center', 'color': '#2c3e50', 'marginBottom': '20px', 'fontSize': '1.5em'
        }),
        dcc.Graph(
            id='changes-bar-chart-2d',
            # figure zostanie zaktualizowane przez callback
        )
    ]),

    # Kontener dla Wykresu Rozkładu Typów Zadań
    html.Div(style={
        'backgroundColor': '#ffffff',
        'borderRadius': '12px',
        'boxShadow': '0 4px 20px rgba(0, 0, 0, 0.08)',
        'padding': '30px',
        'width': '100%',
        'maxWidth': '1000px',
        'marginBottom': '40px'
    }, children=[
        html.H3(children='Rozkład Typów Zadań w Kwartałach', style={
            'textAlign': 'center', 'color': '#2c3e50', 'marginBottom': '20px', 'fontSize': '1.5em'
        }),
        dcc.Graph(
            id='issue-type-breakdown-chart',
            # figure zostanie zaktualizowane przez callback
        )
    ]),

    # Kontener dla szczegółów zadań (bez zmian)
    html.Div(style={
        'backgroundColor': '#ffffff',
        'borderRadius': '12px',
        'boxShadow': '0 4px 20px rgba(0, 0, 0, 0.08)',
        'padding': '30px',
        'width': '100%',
        'maxWidth': '1000px',
        'minHeight': '200px'
    }, children=[
        html.H2(children='Szczegóły Zadań (Kliknij na słupek na wykresie Platform)', style={
            'textAlign': 'center', 
            'color': '#2c3e50', 
            'marginBottom': '20px',
            'fontSize': '1.8em',
            'fontWeight': 'semibold'
        }),
        html.Div(id='click-data-output', style={
            'whiteSpace': 'pre-wrap', 
            'backgroundColor': '#ecf0f1', 
            'border': '1px solid #bdc3c7', 
            'borderRadius': '8px', 
            'padding': '20px', 
            'fontFamily': 'monospace', 
            'fontSize': '0.9em',
            'color': '#2c3e50',
            'maxHeight': '400px', 
            'overflowY': 'auto'
        })
    ])
])

# --- Callback do aktualizacji wykresów i KPI na podstawie filtrów ---
@app.callback(
    Output('changes-bar-chart-2d', 'figure'),
    Output('issue-type-breakdown-chart', 'figure'),
    Output('kpi-q1-total', 'children'),
    Output('kpi-q2-total', 'children'),
    Output('kpi-total-overall', 'children'),
    Input('quarter-filter', 'value'),
    Input('platform-filter', 'value')
)
def update_charts_and_kpis(selected_quarter_value, selected_platform_value):
    # Ponownie przetwórz dane z filtrami
    filtered_categorized_results, filtered_issue_type_breakdown = categorize_and_filter_changes(
        df_raw_global, selected_quarter=selected_quarter_value, selected_platform=selected_platform_value
    )

    # Aktualizacja KPI
    total_q1 = sum(filtered_categorized_results["Q1 2025"])
    total_q2 = sum(filtered_categorized_results["Q2 2025"])
    total_overall = total_q1 + total_q2

    # Przygotowanie danych dla wykresu 2D (Platforma vs Liczba Zadań)
    # df_plot_2d_filtered musi odzwierciedlać tylko wybrane platformy
    current_platforms_for_display = filtered_categorized_results["Platforma"] # Lista platform po filtrowaniu

    plot_data_2d_filtered_items = []
    for platform in current_platforms_for_display:
        platform_idx = filtered_categorized_results["Platforma"].index(platform)
        plot_data_2d_filtered_items.append({
            "Platforma": platform,
            "Liczba zadań": filtered_categorized_results["Q1 2025"][platform_idx],
            "Kwartał": "Q1 2025"
        })
        plot_data_2d_filtered_items.append({
            "Platforma": platform,
            "Liczba zadań": filtered_categorized_results["Q2 2025"][platform_idx],
            "Kwartał": "Q2 2025"
        })
    df_plot_2d_filtered = pd.DataFrame(plot_data_2d_filtered_items)

    fig_2d = px.bar(df_plot_2d_filtered, 
                    x='Platforma', 
                    y='Liczba zadań', 
                    color='Kwartał', 
                    barmode='group',
                    title='Zakończone Zadania według Platform i Kwartałów',
                    labels={'Liczba zadań': 'Liczba Zadań', 'Platforma': 'Platforma / Kategoria'},
                    color_discrete_map={
                        'Q1 2025': '#2ecc71', 
                        'Q2 2025': '#3498db'  
                    },
                    hover_data={'Kwartał': True, 'Liczba zadań': True, 'Platforma': False},
                    template="plotly_white"
                   ).update_layout(
                       title_x=0.5, 
                       font_size=14, 
                       title_font_size=20,
                       xaxis_title_font_size=16,
                       yaxis_title_font_size=16,
                       legend_title_font_size=14,
                       legend_font_size=12
                   )

    # Przygotowanie danych dla wykresu rozkładu typów zadań (Issue Type Breakdown)
    issue_type_data_filtered = []
    current_q1_types = filtered_issue_type_breakdown.get('Q1 2025', {})
    current_q2_types = filtered_issue_type_breakdown.get('Q2 2025', {})

    # Zbierz wszystkie unikalne typy zadań zebrane przez categorize_and_filter_changes
    all_issue_types_in_filtered_data = sorted(list(set(list(current_q1_types.keys()) + list(current_q2_types.keys()))))

    for issue_type in all_issue_types_in_filtered_data:
        issue_type_data_filtered.append({'Kwartał': 'Q1 2025', 'Typ Zadania': issue_type, 'Liczba': current_q1_types.get(issue_type, 0)})
        issue_type_data_filtered.append({'Kwartał': 'Q2 2025', 'Typ Zadania': issue_type, 'Liczba': current_q2_types.get(issue_type, 0)})

    df_issue_type_filtered = pd.DataFrame(issue_type_data_filtered)

    fig_issue_type = px.bar(df_issue_type_filtered,
                            x='Kwartał',
                            y='Liczba',
                            color='Typ Zadania',
                            barmode='stack',
                            title='Rozkład Zakończonych Zadań według Typu (Q1 vs Q2)',
                            labels={'Liczba': 'Liczba Zadań', 'Typ Zadania': 'Typ Zadania'},
                            template="plotly_white",
                            hover_data={'Liczba': True, 'Kwartał': False, 'Typ Zadania': True}
                           ).update_layout(
                               title_x=0.5,
                               font_size=14,
                               title_font_size=20,
                               xaxis_title_font_size=16,
                               yaxis_title_font_size=16,
                               legend_title_font_size=14,
                               legend_font_size=12
                           )
    
    return fig_2d, fig_issue_type, total_q1, total_q2, total_overall


# --- Callback do wyświetlania szczegółów po kliknięciu na słupek (tylko z wykresu 2D Platform) ---
@app.callback(
    Output('click-data-output', 'children'),
    Input('changes-bar-chart-2d', 'clickData'),
    Input('quarter-filter', 'value'), # Potrzebne do odświeżenia szczegółów po zmianie filtra
    Input('platform-filter', 'value') # Potrzebne do odświeżenia szczegółów po zmianie filtra
)
def display_click_data(clickData, selected_quarter_value, selected_platform_value):
    # Wczytujemy dane ponownie z uwzględnieniem aktywnych filtrów,
    # aby szczegóły wyświetlały tylko to, co jest faktycznie przefiltrowane
    current_categorized_results, _ = categorize_and_filter_changes(
        df_raw_global, selected_quarter=selected_quarter_value, selected_platform=selected_platform_value
    )

    if clickData is None:
        return "Kliknij na słupek na wykresie Platform, aby zobaczyć szczegóły zadań."
    
    point_data = clickData['points'][0]
    platform = point_data['x']
    quarter = point_data['customdata'][0] 

    details_key = f"Details {quarter}"
    
    details_list = []
    # Używamy current_categorized_results, aby szczegóły były zgodne z filtrami
    if details_key in current_categorized_results and platform in current_categorized_results[details_key]:
        details_list = current_categorized_results[details_key][platform]

    if details_list:
        return f"Szczegóły zadań dla {platform} w {quarter}:\n\n" + "\n".join(sorted(list(set(details_list))))
    else:
        return f"Brak szczegółów zadań dla {platform} w {quarter}."


# --- 4. Uruchomienie serwera aplikacji ---
if __name__ == '__main__':
    app.run(debug=True)