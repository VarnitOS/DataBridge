export async function parseCSV(file: File): Promise<Record<string, any>[]> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    
    reader.onload = (e) => {
      try {
        const text = e.target?.result as string;
        const lines = text.split('\n').filter(line => line.trim());
        
        if (lines.length === 0) {
          resolve([]);
          return;
        }
        
        // Parse header
        const headers = lines[0].split(',').map(h => h.trim().replace(/^"|"$/g, ''));
        
        // Parse data rows
        const data = lines.slice(1).map(line => {
          const values = line.split(',').map(v => v.trim().replace(/^"|"$/g, ''));
          const row: Record<string, any> = {};
          
          headers.forEach((header, index) => {
            row[header] = values[index] || '';
          });
          
          return row;
        });
        
        resolve(data);
      } catch (error) {
        reject(error);
      }
    };
    
    reader.onerror = () => reject(reader.error);
    reader.readAsText(file);
  });
}

export function getFieldNames(data: Record<string, any>[]): string[] {
  if (data.length === 0) return [];
  return Object.keys(data[0]);
}

export function generateMockBankData(type: 'source' | 'target'): Record<string, any>[] {
  if (type === 'source') {
    return [
      { account_num: 'ACC001', client_name: 'John Smith', bal: '$45,230.50', branch: 'NY-001', acct_type: 'Savings' },
      { account_num: 'ACC002', client_name: 'Sarah Johnson', bal: '$128,450.00', branch: 'NY-002', acct_type: 'Checking' },
      { account_num: 'ACC003', client_name: 'Michael Brown', bal: '$67,890.25', branch: 'NY-001', acct_type: 'Savings' },
      { account_num: 'ACC004', client_name: 'Emily Davis', bal: '$234,100.75', branch: 'LA-001', acct_type: 'Investment' },
      { account_num: 'ACC005', client_name: 'David Wilson', bal: '$89,450.00', branch: 'LA-002', acct_type: 'Checking' },
    ];
  } else {
    return [
      { account_number: 'TGT101', customer_name: 'Robert Taylor', balance: '$156,780.00', branch_code: 'CH-001', account_type: 'Savings' },
      { account_number: 'TGT102', customer_name: 'Lisa Anderson', balance: '$98,450.50', branch_code: 'CH-002', account_type: 'Checking' },
      { account_number: 'TGT103', customer_name: 'James Martinez', balance: '$203,890.25', branch_code: 'CH-001', account_type: 'Investment' },
      { account_number: 'TGT104', customer_name: 'Jennifer Garcia', balance: '$74,230.00', branch_code: 'SF-001', account_type: 'Savings' },
      { account_number: 'TGT105', customer_name: 'William Rodriguez', balance: '$145,670.75', branch_code: 'SF-002', account_type: 'Checking' },
    ];
  }
}
