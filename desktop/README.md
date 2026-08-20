# Desktop client (tkinter)

Simple desktop UI for the Django auth API.

## Screens

| Tab | Features |
|-----|----------|
| **Login** | email + password, forgot password |
| **Register** | username, password, confirm, email, first/last name, phone |
| **Profile** | edit first/last/phone, change password |
| **Data** | placeholder for your custom model |

## Setup

1. Start the Django backend:

```bash
cd back
python manage.py migrate
python manage.py runserver
```

2. Install desktop deps and run:

```bash
cd desktop
pip install -r requirements.txt
python app.py
```

> **Note:** tkinter ships with most Python installs on Windows/macOS.  
> On Linux you may need: `sudo apt install python3-tk`

## API base URL

Default is `http://127.0.0.1:8000/api`.  
If you use another port (e.g. `8001`), edit the last lines of `app.py`:

```python
app = AuthApp(api_base="http://127.0.0.1:8001/api")
```
