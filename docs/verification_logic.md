# Verification logic

Requirements are configurable in `app.py` by loan type. The default personal-loan demo checklist is PAN, identity proof, three salary slips, six months of bank statements, and employment proof.

Checks use normalized exact/containment name comparisons, a structural PAN pattern check, declared-vs-payslip income threshold of 10%, recurring bank credit comparison, uploaded file hashes, required document counts, and simple statement month coverage. Confidence reflects extraction evidence quality and is not a probability of default or fraud. OCR-unavailable and unreadable data must remain unknown rather than be inferred as a pass.

Salary differences, missing periods and duplicates are review indicators. Reports show the evidence, possible benign explanations and next steps. A human reviewer remains responsible for lending decisions.
