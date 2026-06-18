export interface Customer {
  id: string
  label: string
  languages: string[]  // language IDs available for this customer
  disabled?: boolean
}

export const CUSTOMERS: Customer[] = [
  { id: 'ldpov', label: 'LDPoV', languages: ['python', 'javascript', 'java'] },
  { id: 'aspov', label: 'ASPoV', languages: ['python', 'javascript'], disabled: true },
]

export function getCustomer(id: string): Customer {
  return CUSTOMERS.find(c => c.id === id) ?? CUSTOMERS[0]
}

export const DEFAULT_CUSTOMER = CUSTOMERS[0].id
