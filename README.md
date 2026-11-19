# LoanDocVerify

LoanDocVerify is a demonstration of loan application intake, document verification, evidence review, and applicant/officer collaboration. Each installation stores its own accounts, applications, and uploads.

## Publish a free shared demo website

The repository does not host a live website by itself. For a free hosted demo with persistent SQLite data and uploaded files, use PythonAnywhere's free web app. This repository includes [`pythonanywhere_wsgi.py`](pythonanywhere_wsgi.py), an adapter for its managed WSGI server.

### Deploy on PythonAnywhere

1. Create or sign in to a PythonAnywhere account and open a Bash console from **Consoles**.
2. Clone the repository and install the dependencies:

   ```sh
   git clone https://github.com/TVSVEN/LoanDOC-Verify.git
   cd LoanDOC-Verify
   python3.12 -m venv ~/.virtualenvs/loandocverify
   ~/.virtualenvs/loandocverify/bin/pip install -r requirements.txt
   ```

3. Open **Web > Add a new web app**, select the free `your-username.pythonanywhere.com` domain, choose **Manual configuration**, and select **Python 3.12**.
4. In the **Virtualenv** section, enter `/home/YOUR_USERNAME/.virtualenvs/loandocverify` (replace `YOUR_USERNAME`).
5. Open the WSGI configuration file linked in the **Code** section. Replace its contents with:

   ```python
   import sys

   project = "/home/YOUR_USERNAME/LoanDOC-Verify"
   if project not in sys.path:
       sys.path.insert(0, project)

   from pythonanywhere_wsgi import application
   ```

   Replace `YOUR_USERNAME` with the username shown in your PythonAnywhere account.

6. Save the WSGI file and click **Reload** on the Web tab. Open `https://YOUR_USERNAME.pythonanywhere.com`.
7. Create separate Applicant and Loan officer accounts on this hosted instance. Accounts and uploads from your local Docker installation are separate and are not copied over.
8. After the site is live, add its URL to this repository's GitHub **About > Website** field and replace the **Live website** line below.

**Live website:** Not deployed yet. Add the PythonAnywhere URL here after deployment.

### Free hosting limits

PythonAnywhere currently lists 512 MiB of disk space, one web app with one worker, and a one-month web-app expiry for free accounts. Renew the demo from the PythonAnywhere dashboard when it approaches expiry. Uploaded files and the SQLite database use that disk quota and persist in the account's home directory. See [PythonAnywhere free account features](https://help.pythonanywhere.com/pages/FreeAccountsFeatures/).

Use synthetic documents only. This project does not include the security, privacy, email recovery, malware scanning, monitoring, or compliance controls required for production lending data.

## Run on Windows, macOS, or Linux

### Requirements

- Git
- Docker Desktop on Windows/macOS, or Docker Engine and the Docker Compose plugin on Linux
- Docker must be running

### Start the website

1. Clone the repository and open a terminal in the project folder:

   ```sh
   git clone <repository-url>
   cd <repository-folder>
   ```

2. Start LoanDocVerify:

   ```sh
   docker compose up --build -d
   ```

3. Open [http://127.0.0.1:8000](http://127.0.0.1:8000) in a browser.

The first start builds the container and initializes a local database. Create an Applicant account to submit an application. Create a separate Loan officer account to review applications. Use the applicant’s one-time invitation code to link the application to the officer account.

### Stop, restart, and troubleshoot

- Stop the website while preserving data: `docker compose down`
- Start it again: `docker compose up -d`
- View startup logs: `docker compose logs -f`
- Check service health: `docker compose ps`
- Rebuild after pulling code changes: `docker compose up --build -d`

The database and uploaded files live in the Docker volume `loandocverify-data`, so stopping or rebuilding the container preserves them. To intentionally delete this installation’s saved data, run `docker compose down -v` (this permanently removes that Compose volume).

### Change the local port

If port 8000 is already in use, copy `.env.example` to `.env`, change `LDV_PORT` (for example, `LDV_PORT=8001`), and run `docker compose up --build -d`. Then open `http://127.0.0.1:8001`.

By default, the app listens only on this computer. To make it reachable by other devices on the same trusted network, set `LDV_BIND_ADDRESS=0.0.0.0` in `.env` and allow the selected port through the computer’s firewall. Do not expose this demo directly to the public internet.

## Run without Docker (Windows)

Install Python 3.10 or newer, then double-click **Open LoanDocVerify.bat**. Keep its console window open while using the site. The server and database run on that computer; open `http://127.0.0.1:8000` if the browser does not open automatically.

To run manually on any platform:

```sh
python -m pip install -r requirements.txt
python app.py
```

## Applicant and loan officer walkthrough

1. Create an Applicant account and submit an application. Add the supporting files under **Documents**.
2. On Applicant **Overview**, select **Share with loan officer**. Give the one-time code to the intended officer.
3. Sign out and sign in to a separate Loan officer account. Under **Applications**, choose **Link applicant application** and enter the code.
4. Open the linked application, inspect its source documents, and start verification.
5. Expand findings to see explanations and source evidence. If information is missing or inconsistent, the officer can request clarification.
6. The applicant responds under **Requests**. The officer reviews the response and reruns verification.
7. Review the activity and review history. Export an evidence report from **Reports** or the case workspace.

## Data and installation boundaries

Each clone and Docker Compose project has a separate database and file store. Accounts and invitation codes work only within the same running installation; separate users’ computers do not synchronize data automatically. To collaborate across computers, the app needs to be deployed as one shared service with durable storage and suitable access controls.

The default Compose port is bound to localhost. The app uses password authentication, one role per account, application ownership, and explicit officer invitations. A local single-user deployment is intended for synthetic demonstrations and development.

## Demo limitations and safety

This is not a production lending system. Use synthetic documents only. Signup does not include email verification or organization-admin approval. The app has no external identity or banking checks, malware scanning, production retention controls, or full enterprise audit/security controls. Image OCR is not implemented; scanned images may be marked **OCR needed**. Verification findings support a human review and never approve or decline a loan.

The verification rules are deterministic examples documented in [verification logic](docs/verification_logic.md). See also [architecture](docs/architecture.md), [UI behavior](docs/ui_behavior.md), and [database schema](database/schema.sql).
