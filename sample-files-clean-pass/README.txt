LoanDocVerify clean-pass sample files
====================================

Use these fictional files for a deterministic clean-pass demonstration. Do not use real personal or financial data.

Create a NEW Personal Loan application with these exact values:
Applicant name: Demo Applicant
Date of birth: 12/06/1994
Phone: +91 90000 10001
Email: demo.applicant@example.test
Requested amount: 500000
Purpose: Home renovation
Employment type: Salaried
Employer: Northstar Analytics
Declared monthly income: 75000

Upload each of these seven TXT files once:
1. PAN_Demo_Applicant.txt -> PAN
2. Aadhaar_Demo_Applicant.txt -> Aadhaar
3. Salary_Slip_January_2026.txt -> Salary Slip
4. Salary_Slip_February_2026.txt -> Salary Slip
5. Salary_Slip_March_2026.txt -> Salary Slip
6. Bank_Statement_January_to_June_2026.txt -> Bank Statement
7. Employment_Proof_Northstar_Analytics.txt -> Employment Proof

The app should classify from the filename/content. Confirm the category in Documents before running verification. If classification is wrong, correct it there first.

Expected clean-pass: all required categories present; identity name and date match; employer matches; declared income, payslips and six monthly bank credits all equal 75000; no duplicate uploads; all files are readable text. The result is a demonstration of configured rules, not a lending decision.

Important: these documents will correctly match only the exact application values above. Do not upload them to Rahul Sharma, Thejas, or another application with different details. If verification was already run on an application, correct the details/documents and start verification again so the stale findings are replaced.

These TXT files have machine-readable text; they do not demonstrate image OCR. The app's current image handling reports OCR needed because it does not run an OCR engine. A scanned image cannot be promised to verify automatically in this version.
