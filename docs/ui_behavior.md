# UI behavior map

## Applicant portal

- **Overview** shows application status, the progress stepper, open requests, the document checklist, and recent messages.
- **My application** displays submitted details and opens the same validated multi-step form for edits.
- **Documents** accepts drag/drop or file selection, reports upload progress, and connects preview, replace, remove, and officer-side type correction to the API.
- **Verification** filters checks and expands each check into a source-backed explanation. Applicants can open the cited source file.
- **Requests** lets the applicant attach one supporting file, add a message, and submit a response. Request history stays with the application.
- **Help** explains the review process and the human decision boundary.

## Officer workspace

- **Overview** cards link to filtered cases; the queue preview and agent events open their application.
- **Applications** supports name/ID search, status and loan type filters, sortable columns, and pagination.
- **Review queue** lists cases that still have an open review record.
- **Case workspace** has Summary, Documents, Verification, Agent activity, and Review history tabs. A finding can be expanded, its cited document opened, and an officer assessment recorded with a note where required.
- **Request, assign, note, assess, resolve, document update, and document delete** actions are persisted and add application events. Resolving a review case never changes the lending decision.
- **Reports** previews and downloads a PDF built from the current persisted application, source document list, checks, evidence, events, and limitations.
- **Agent activity** displays stored action summaries. The case screen may replay the stored event list as a labeled deterministic demo playback; it does not stream fabricated events.
- **Settings** saves notification and reduced-motion preferences in the local browser and documents the sample verification rules.

## Data and access boundary

Applicant and loan officer are separate, fixed account roles. An applicant owns their applications and must explicitly share one with an officer through a one-time invitation code. The officer must sign in to their own account and accept the code before the application appears in their workspace. Applicant access remains available to the owner. Each local installation has its own database and uploads.

Use synthetic examples only. Image OCR and external applicant communications are not available in this local MVP. A readable-text absence is shown as an OCR/readability limitation, never treated as a successful extraction.
