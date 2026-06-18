import { createContext, useContext, useState } from 'react'
import type { ReactNode } from 'react'
import { DEFAULT_CUSTOMER } from '../customers'

interface CustomerContextValue {
  customerId: string
  setCustomerId: (id: string) => void
}

const CustomerContext = createContext<CustomerContextValue>({
  customerId: DEFAULT_CUSTOMER,
  setCustomerId: () => {},
})

export function CustomerProvider({ children }: { children: ReactNode }) {
  const [customerId, setCustomerId] = useState(DEFAULT_CUSTOMER)
  return (
    <CustomerContext.Provider value={{ customerId, setCustomerId }}>
      {children}
    </CustomerContext.Provider>
  )
}

export function useCustomer() {
  return useContext(CustomerContext)
}
