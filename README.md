# Holiday Episodes Dashboard

Interactive Plotly Dash dashboard for the DSA2101 Holiday Episodes analysis. (https://holiday-episodes-dashboard.onrender.com)

## Features
- **Overview** – summary statistics & holiday-type breakdown
- **Genre Vote Share** – stacked bar chart of genre proportions by decade (interactive genre selector)
- **Runtime vs Rating** – 2D KDE density plots with sweet-spot annotations per genre
- **Data Table** – searchable/sortable top-500 episodes

## Local Run

```bash
pip install -r requirements.txt
python app.py
```

## File Structure

```
holiday-dashboard/
├── app.py              # Main Dash application
├── requirements.txt    # Python dependencies
├── Procfile            # For Render / Heroku
├── README.md
└── data/
    ├── holiday_episodes.csv
    └── holiday_genres.csv
```
