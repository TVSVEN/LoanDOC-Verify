export const personalLoanChecklist = [
  { type: 'PAN', label: 'PAN', minimum: 1 },
  { type: 'Aadhaar', label: 'Identity proof (Aadhaar or other government ID)', minimum: 1 },
  { type: 'Salary Slip', label: 'Three recent salary slips', minimum: 3 },
  { type: 'Bank Statement', label: 'Six-month bank statement', minimum: 1 },
  { type: 'Employment Proof', label: 'Employment proof', minimum: 1 },
];

export function checklistCount(application, type) {
  return (application.documents || []).filter((document) =>
    document.document_type === type ||
    (type === 'Aadhaar' && document.document_type === 'Identity Proof')
  ).length;
}

export function checklistStatus(count, minimum) {
  if (count >= minimum) return 'Received';
  return count ? `${count} of ${minimum} received` : 'Needed';
}

export function classificationOptions(selectedType, escapeHtml) {
  const knownType = personalLoanChecklist.some((item) => item.type === selectedType);
  const placeholder = !knownType
    ? '<option value="" selected disabled>Select a checklist category…</option>'
    : '';
  return placeholder + personalLoanChecklist.map((item) =>
    `<option value="${item.type}" ${item.type === selectedType ? 'selected' : ''}>${escapeHtml(item.label)}</option>`
  ).join('');
}
