import { createContext, useContext, useState, useCallback, useEffect } from 'react'
import api, { endpoints } from './api'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isAuthenticated, setIsAuthenticated] = useState(false)

  const fetchUser = useCallback(async () => {
    try {
      const response = await api.get(endpoints.authUser)
      if (response.data && response.data.pk) {
        setUser(response.data)
        setIsAuthenticated(true)
      } else {
        setUser(null)
        setIsAuthenticated(false)
      }
    } catch (error) {
      setUser(null)
      setIsAuthenticated(false)
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchUser()
  }, [fetchUser])

  const login = useCallback(async (username, password) => {
    try {
      await api.post(endpoints.authLogin, { username, password })
      await fetchUser()
      return { success: true }
    } catch (error) {
      return {
        success: false,
        error: error.response?.data?.detail || 'Échec de la connexion',
      }
    }
  }, [fetchUser])

  const logout = useCallback(async () => {
    try {
      await api.post(endpoints.authLogout)
    } catch (error) {
      console.error('Logout error:', error)
    }
    setUser(null)
    setIsAuthenticated(false)
  }, [])

  const checkIsAdmin = useCallback(() => {
    if (!user) return false
    return user.is_superuser || user.is_staff || false
  }, [user])

  const value = {
    user,
    isAuthenticated,
    isLoading,
    login,
    logout,
    isAdmin: checkIsAdmin(),
    refreshUser: fetchUser,
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}