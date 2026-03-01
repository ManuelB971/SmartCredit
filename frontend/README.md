# Frontend - Smart Crédit

## Structure

```
frontend/
├── templates/           # HTML templates
│   ├── base.html        # Base layout
│   ├── home.html        # Homepage
│   ├── wizard/          # 3-step wizard
│   └── results/         # Results pages
└── static/             # Assets
    ├── css/            # Stylesheets
    ├── js/             # JavaScript
    └── img/            # Images
```

## Templates

### base.html
Master template with Tabler Bootstrap setup.

### Wizard
- **step1_profil.html**: Personal information
- **step2_revenus.html**: Income & charges
- **step3_projet.html**: Credit details
- **step4_loading.html**: Processing animation

### Results
- **results.html**: Main results with score
- **comparison.html**: Scenario comparison

## Static Files

### CSS
- **style.css**: Custom styles

### JavaScript
- **main.js**: Wizard form handling, API calls

## Frontend Flow

1. User selects credit type (home.html)
2. Fills 3-step wizard form
3. API creates simulation + runs calculation
4. Shows results with IA explanation
5. Option to export PDF/email
