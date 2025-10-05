// Simulates Google Gemini AI-powered field mapping

interface FieldMapping {
  sourceField: string;
  targetField: string;
  confidence: number;
  status: 'confirmed' | 'suggested' | 'manual';
}

// Common financial field patterns and their variations
const fieldSynonyms: Record<string, string[]> = {
  'account_number': ['account_num', 'acct_number', 'account_id', 'acct_no', 'account'],
  'customer_name': ['client_name', 'name', 'customer', 'client', 'full_name'],
  'balance': ['amount', 'account_balance', 'current_balance', 'bal'],
  'transaction_date': ['date', 'trans_date', 'transaction_dt', 'txn_date'],
  'transaction_id': ['trans_id', 'txn_id', 'transaction_number', 'reference'],
  'branch_code': ['branch', 'branch_id', 'location_code', 'branch_number'],
  'email': ['email_address', 'contact_email', 'e_mail'],
  'phone': ['phone_number', 'contact_number', 'telephone', 'mobile'],
  'address': ['street_address', 'location', 'full_address'],
  'account_type': ['type', 'acct_type', 'product_type'],
};

function calculateSimilarity(str1: string, str2: string): number {
  const s1 = str1.toLowerCase().replace(/[_\s-]/g, '');
  const s2 = str2.toLowerCase().replace(/[_\s-]/g, '');
  
  // Exact match
  if (s1 === s2) return 1.0;
  
  // Check synonyms
  for (const [canonical, synonyms] of Object.entries(fieldSynonyms)) {
    const allVariants = [canonical, ...synonyms];
    if (allVariants.some(v => v.replace(/[_\s-]/g, '') === s1) && 
        allVariants.some(v => v.replace(/[_\s-]/g, '') === s2)) {
      return 0.95;
    }
  }
  
  // Substring match
  if (s1.includes(s2) || s2.includes(s1)) {
    return 0.75;
  }
  
  // Levenshtein-inspired simple similarity
  const longer = s1.length > s2.length ? s1 : s2;
  const shorter = s1.length > s2.length ? s2 : s1;
  
  let matches = 0;
  for (let i = 0; i < shorter.length; i++) {
    if (longer.includes(shorter[i])) matches++;
  }
  
  return matches / longer.length;
}

export function generateAIMappings(
  sourceFields: string[],
  targetFields: string[]
): FieldMapping[] {
  const mappings: FieldMapping[] = [];
  const usedTargets = new Set<string>();
  
  // First pass: high confidence matches
  for (const sourceField of sourceFields) {
    let bestMatch = { field: '', confidence: 0 };
    
    for (const targetField of targetFields) {
      if (usedTargets.has(targetField)) continue;
      
      const confidence = calculateSimilarity(sourceField, targetField);
      if (confidence > bestMatch.confidence) {
        bestMatch = { field: targetField, confidence };
      }
    }
    
    if (bestMatch.confidence > 0.5) {
      usedTargets.add(bestMatch.field);
      mappings.push({
        sourceField,
        targetField: bestMatch.field,
        confidence: bestMatch.confidence,
        status: bestMatch.confidence > 0.8 ? 'confirmed' : 'suggested'
      });
    }
  }
  
  return mappings;
}

export function mergeDatasets(
  sourceData: Record<string, any>[],
  targetData: Record<string, any>[],
  mappings: FieldMapping[]
): Record<string, any>[] {
  const mergedData: Record<string, any>[] = [];
  
  // Transform source data using mappings
  const transformedSource = sourceData.map(row => {
    const newRow: Record<string, any> = {};
    mappings.forEach(mapping => {
      if (row.hasOwnProperty(mapping.sourceField)) {
        newRow[mapping.targetField] = row[mapping.sourceField];
      }
    });
    return newRow;
  });
  
  // Combine with target data
  mergedData.push(...transformedSource);
  mergedData.push(...targetData);
  
  return mergedData;
}
