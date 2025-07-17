import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { 
  User, 
  Request, 
  Transaction, 
  City, 
  RequestType, 
  Direction, 
  Master, 
  AdvertisingCampaign,
  TransactionType,
  Role
} from '../types';

interface AppState {
  // User state
  user: User | null;
  setUser: (user: User | null) => void;
  
  // Requests state
  requests: Request[];
  setRequests: (requests: Request[]) => void;
  addRequest: (request: Request) => void;
  updateRequest: (id: number, updates: Partial<Request>) => void;
  removeRequest: (id: number) => void;
  
  // Transactions state
  transactions: Transaction[];
  setTransactions: (transactions: Transaction[]) => void;
  addTransaction: (transaction: Transaction) => void;
  updateTransaction: (id: number, updates: Partial<Transaction>) => void;
  removeTransaction: (id: number) => void;
  
  // Reference data
  cities: City[];
  setCities: (cities: City[]) => void;
  requestTypes: RequestType[];
  setRequestTypes: (types: RequestType[]) => void;
  directions: Direction[];
  setDirections: (directions: Direction[]) => void;
  masters: Master[];
  setMasters: (masters: Master[]) => void;
  advertisingCampaigns: AdvertisingCampaign[];
  setAdvertisingCampaigns: (campaigns: AdvertisingCampaign[]) => void;
  transactionTypes: TransactionType[];
  setTransactionTypes: (types: TransactionType[]) => void;
  roles: Role[];
  setRoles: (roles: Role[]) => void;
  
  // UI state
  isLoading: boolean;
  setLoading: (loading: boolean) => void;
  error: string | null;
  setError: (error: string | null) => void;
  
  // Filters
  requestFilters: {
    status: string;
    city_id: string;
    master_id: string;
    date_from: string;
    date_to: string;
    search: string;
  };
  setRequestFilters: (filters: Partial<AppState['requestFilters']>) => void;
  resetRequestFilters: () => void;
}

const initialRequestFilters = {
  status: '',
  city_id: '',
  master_id: '',
  date_from: '',
  date_to: '',
  search: ''
};

export const useAppStore = create<AppState>()(
  persist(
    (set) => ({
      // User state
      user: null,
      setUser: (user) => set({ user }),
      
      // Requests state
      requests: [],
      setRequests: (requests) => set({ requests }),
      addRequest: (request) => set((state) => ({ requests: [...state.requests, request] })),
      updateRequest: (id, updates) => set((state) => ({
        requests: state.requests.map(req => req.id === id ? { ...req, ...updates } : req)
      })),
      removeRequest: (id) => set((state) => ({
        requests: state.requests.filter(req => req.id !== id)
      })),
      
      // Transactions state
      transactions: [],
      setTransactions: (transactions) => set({ transactions }),
      addTransaction: (transaction) => set((state) => ({ 
        transactions: [...state.transactions, transaction] 
      })),
      updateTransaction: (id, updates) => set((state) => ({
        transactions: state.transactions.map(trans => 
          trans.id === id ? { ...trans, ...updates } : trans
        )
      })),
      removeTransaction: (id) => set((state) => ({
        transactions: state.transactions.filter(trans => trans.id !== id)
      })),
      
      // Reference data
      cities: [],
      setCities: (cities) => set({ cities }),
      requestTypes: [],
      setRequestTypes: (requestTypes) => set({ requestTypes }),
      directions: [],
      setDirections: (directions) => set({ directions }),
      masters: [],
      setMasters: (masters) => set({ masters }),
      advertisingCampaigns: [],
      setAdvertisingCampaigns: (advertisingCampaigns) => set({ advertisingCampaigns }),
      transactionTypes: [],
      setTransactionTypes: (transactionTypes) => set({ transactionTypes }),
      roles: [],
      setRoles: (roles) => set({ roles }),
      
      // UI state
      isLoading: false,
      setLoading: (isLoading) => set({ isLoading }),
      error: null,
      setError: (error) => set({ error }),
      
      // Filters
      requestFilters: initialRequestFilters,
      setRequestFilters: (filters) => set((state) => ({
        requestFilters: { ...state.requestFilters, ...filters }
      })),
      resetRequestFilters: () => set({ requestFilters: initialRequestFilters })
    }),
    {
      name: 'app-store',
      partialize: (state) => ({
        user: state.user,
        cities: state.cities,
        requestTypes: state.requestTypes,
        directions: state.directions,
        masters: state.masters,
        advertisingCampaigns: state.advertisingCampaigns,
        transactionTypes: state.transactionTypes,
        roles: state.roles
      })
    }
  )
);

// Селекторы для оптимизации
export const useUser = () => useAppStore((state) => state.user);
export const useRequests = () => useAppStore((state) => state.requests);
export const useTransactions = () => useAppStore((state) => state.transactions);
export const useCities = () => useAppStore((state) => state.cities);
export const useRequestTypes = () => useAppStore((state) => state.requestTypes);
export const useDirections = () => useAppStore((state) => state.directions);
export const useMasters = () => useAppStore((state) => state.masters);
export const useAdvertisingCampaigns = () => useAppStore((state) => state.advertisingCampaigns);
export const useRequestFilters = () => useAppStore((state) => state.requestFilters);
export const useLoading = () => useAppStore((state) => state.isLoading);
export const useError = () => useAppStore((state) => state.error); 