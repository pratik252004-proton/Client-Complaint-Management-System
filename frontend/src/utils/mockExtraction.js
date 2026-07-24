
const SAMPLE_EXTRACTIONS = [
  {
    complaintSource: 'Email',
    customerName: 'MedCore Distributors Pvt. Ltd.',
    productName: 'Amoxicillin Trihydrate',
    productStrength: '500mg Capsules',
    batchLotNumber: 'AMX-2026-0417',
    manufacturingDate: '2026-02-10',
    expiryDate: '2028-02-09',
    quantityAffected: '120',
    complaintType: 'Product Quality - Discoloration',
    complaintDate: '2026-07-20',
    detailedDescription:
      'Customer reports visible yellow discoloration in approximately 15% of capsules from batch AMX-2026-0417. Product was stored per label conditions. No odor abnormality reported. Photos attached.',
    initialSeverity: 'Major',
    priority: 'High'
  },
  {
    complaintSource: 'Customer Portal',
    customerName: 'Sunrise Pharma Retail Chain',
    productName: 'Paracetamol API',
    productStrength: '99.5% Purity',
    batchLotNumber: 'PCM-API-1182',
    manufacturingDate: '2026-01-05',
    expiryDate: '2029-01-04',
    quantityAffected: '25',
    complaintType: 'Packaging Defect',
    complaintDate: '2026-07-18',
    detailedDescription:
      'Outer drum packaging found with a compromised seal on 2 of 25 drums received. Inner liner appears intact. Requesting replacement and root cause investigation.',
    initialSeverity: 'Minor',
    priority: 'Medium'
  }
]

export function runMockExtraction() {
  const sample =
    SAMPLE_EXTRACTIONS[Math.floor(Math.random() * SAMPLE_EXTRACTIONS.length)]
  return new Promise((resolve) => {
    setTimeout(() => resolve(sample), 400)
  })
}
