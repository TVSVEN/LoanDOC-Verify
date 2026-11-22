<img width="1332" height="787" alt="image" src="https://github.com/user-attachments/assets/4492fabf-308c-4cf5-ad31-5a40d864bca2" /># LoanDocVerify
Live Website : https://loandocverify.onrender.com
LoanDocVerify is a demonstration of loan application intake, document verification, evidence review, and applicant/officer collaboration. Each installation stores its own accounts, applications, and uploads.

## Publish a free shared demo website

Deploy the public demo on Render's **Free** web-service plan. The root [`render.yaml`](render.yaml) explicitly selects the free plan and does not request a paid persistent disk, which was why the previous setup asked for payment. Create the service from [this Render deploy link](https://render.com/deploy?repo=https://github.com/TVSVEN/LoanDOC-Verify), sign in, review the service, and deploy it. Render will provide a public `*.onrender.com` URL that works in a browser on Windows, macOS, Linux, phones, and tablets. The GitHub repository remains the source; commits to `main` trigger redeployment.

**Free-plan behavior:** the site may sleep after 15 minutes without visitors and take about a minute to wake. Its filesystem is temporary, so user accounts, applications, and uploads created on the hosted demo reset after a sleep, restart, or redeploy. This is suitable for a synthetic-data demo, not durable records. Create fresh Applicant and Loan officer accounts on the hosted site; local accounts and files are not copied to it. Render documents [free-service limits](https://render.com/docs/free).

**Live website:** https://loandocverify.onrender.com

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
