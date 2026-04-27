# Oracle Setup (A1SATANEST)

## 1) Install Python dependencies

```bash
pip install -r requirements.txt
```

## 2) Configure environment variables

PowerShell example:

```powershell
$env:DB_TYPE="oracle"
$env:ORACLE_USER="your_oracle_user"
$env:ORACLE_PASSWORD="your_oracle_password"
$env:ORACLE_DSN="localhost:1521/XEPDB1"
$env:A1_SECRET_KEY="replace-with-strong-random-secret"
$env:A1_ADMIN_PASSWORD="replace-admin-password"
```

## 3) Run app

```bash
python app.py
```

## Notes

- If `DB_TYPE` is not set, app uses SQLite (`database.db`).
- On first run in Oracle mode, required tables are auto-created.
- Product and review seed data is inserted automatically if tables are empty.
- Use `A1_ADMIN_PASSWORD` to control admin panel login password.
