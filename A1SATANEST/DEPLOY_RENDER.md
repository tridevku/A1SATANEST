# Deploy A1SATANEST on Render (Free Plan)

## 1) Push code to GitHub

1. Create a new GitHub repository.
2. Upload this full project to that repository.

## 2) Deploy on Render

1. Open [https://render.com](https://render.com) and log in with your GitHub account.
2. Click **New +** -> **Blueprint**.
3. Select your GitHub repo.
4. Render will detect `render.yaml` and create the web service on the **free** plan.
5. Click **Apply** / **Create**.

## 3) Admin login after deploy

- Default admin password is set in `render.yaml`:
  - `A1@SecureAdmin`
- Change it in Render dashboard:
  - Service -> **Environment** -> `A1_ADMIN_PASSWORD`

## 4) Important note about free plan + SQLite

- Current setup uses `DB_TYPE=sqlite`.
- On free plan, filesystem can reset/redeploy and SQLite data may not be permanent.
- For production persistence, switch to managed DB (Render Postgres / external DB) and update app DB config accordingly.
