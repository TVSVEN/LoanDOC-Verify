LoanDocVerify synthetic test pack
================================

All documents are fictional and for the local demo only.

Create a Personal Loan application with these matching details:
Applicant name: Demo Applicant
Date of birth: 12/06/1994
Phone: +91 90000 10001
Email: demo.applicant@example.test
Requested amount: 500000
Purpose: Home renovation
Employment type: Salaried
Employer: Northstar Analytics
Monthly income: 75000

Baseline pass walkthrough:
1. Upload PAN_Demo_Applicant.txt.
2. Upload Aadhaar_Identity_Demo_Applicant.txt.
3. Upload all three Salary_Slip_*.txt files.
4. Upload Bank_Statement_January_to_June_2026.txt.
5. Upload Employment_Proof_Demo_Applicant.txt.
6. If a file is classified as Other, set Classification to the matching checklist category and save it.
7. Switch to Loan officer, open the application, and choose Start verification.

Expected baseline: required categories are present, all six bank salary credits span January through June 2026, declared income matches payslips and bank credits, and readable text is available. Verification is rule-based demo behavior, not a lending decision.

OCR demonstration:
Upload OCR_Demo_Scanned_Document.png separately after the baseline run, leave it classified as Other, then run verification again. The image has visible text but no machine-readable text layer. This demo has no OCR engine, so the file should show OCR needed / Needs OCR and the readability check should need attention. It will not extract the image text automatically.

Supported upload types include PDF, JPG, PNG, TXT, and CSV. Do not use real personal or financial documents.
