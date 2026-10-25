# Local validation

Use Python 3.12+ and a Node version supported by the pinned Astro release. From the repository root:

```sh
python -m venv .venv
```

Activate it with `.venv\Scripts\Activate.ps1` in Windows PowerShell, or `source .venv/bin/activate` on macOS/Linux. Then:

```sh
python -m pip install -r backend/requirements.txt
cd backend
python manage.py test --settings=config.test_settings
python manage.py makemigrations --check --dry-run --settings=config.test_settings
cd ../frontend
npm ci
npx playwright install chromium firefox
npm run check
npm run build
npm test
```

On Linux, Playwright may require `npx playwright install-deps chromium firefox` once. Browser tests start Django on port 8001 and Astro on 4322, use a disposable SQLite database, and serve a small local video/image fixture. They never use the configured database, Google Drive, or email provider. `TEST_PYTHON` can point to a different Python executable with the backend dependencies installed. Leave ports 8001 and 4322 free.

The suite checks Chromium, Firefox, and a Chromium mobile viewport. Google Drive imports and email delivery still require manual validation with configured services. The résumé PDF endpoint already requires `backend/fonts/DejaVuSans.ttf` and `DejaVuSans-Bold.ttf`, which are absent from the repository. Its test is explicitly skipped until both fonts are supplied; the DOCX endpoint is tested.

## Photography (#5)

With your normal local environment configured, apply migrations with `python manage.py migrate` from `backend`. In Studio, create a public image asset with alternative text, then add a Gallery item with Kind **Photography** and Published enabled. Check `/art/`, `/art/photography/`, next/previous navigation, fullscreen and Escape, and the no-JavaScript fallback. Existing Images and Videos should display their original content separately.

## Footer color mode (#4)

The sun/moon switch is in the footer. A new visitor follows the system light/dark setting, including changes while the page is open. Choosing a mode saves an override under the existing `theme` localStorage key; it persists across pages and synchronizes across tabs. Clear that key to resume following the system. Check both system modes, keyboard activation, blocked storage, and mobile layout. The page also follows the system color scheme without JavaScript.
