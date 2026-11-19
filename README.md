# LoanDocVerify

LoanDocVerify is a local, containerized demonstration of loan application intake, document verification, evidence review, and applicant/officer collaboration. Each installation stores its own accounts, applications, and uploads.

## Publish one shared demo website

The repository does not host a live website by itself. The Render Blueprint below configures one public web service with persistent storage for its SQLite database and uploaded files. Creating that service requires a Render account and a paid web-service plan because Render persistent disks are available on paid services. Review the plan and disk charges in Render before deploying.

1. Push this repository to GitHub, including `render.yaml`.
2. Sign in to Render and choose **New > Blueprint**.
3. Connect `TVSVEN/LoanDOC-Verify`, select the `main` branch, and review the `loandocverify` service and persistent disk.
4. Deploy the Blueprint. Render builds the Dockerfile and assigns the service a public `https://...onrender.com` address.
5. Open that address and create separate Applicant and Loan officer accounts. This hosted instance has its own database; accounts from a local Docker run are not copied to it.
6. In GitHub, open the repository, use the gear next to **About**, paste the Render URL into **Website**, and save. Add the same URL to this README under **Live website**.

**Live website:** Not deployed yet. A public URL can be added here after the Render service is deployed.

The hosted service is for a synthetic-data demonstration only. Do not upload real borrower identity, financial, or loan documents. This project does not include the security, privacy, email recovery, malware scanning, monitoring, or compliance controls required for production lending data. Render's disk-backed service uses one instance and has a short interruption during redeploys; see [Render's persistent disk limitations](https://render.com/docs/disks).

The Blueprint sets automatic deployment to off so repository visitors who create their own Render instance do not have it redeploy unexpectedly when this repository changes. To update the shared demo later, trigger a manual deploy from that service's Render dashboard.

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
