export default defineAppConfig({
  authGuardConfig: {
    defaultAccess: 'authenticated',
    whenUnauthenticated: 'redirectToLanding',
    authLanding: '/dashboard',
    unauthLanding: '/unauthLanding',
    routes: {
      unauthenticated: [
        '/unauthLanding',
        '/login',
        '/logout',
        '/register',
        '/forgot-password',
        '/public',
        '/about',
        '/onboarding',
        '/verify-otp',
        '/setup-profile',
        '/api/health',
        '/api/info',
        '/verify'
      ],
      tempAuthenticated: [],
      authenticated: []
    }
  },
  authRoutes: [
    { routeFilter: /^\/apps(\/|$)/, roles: [] },
    { routeFilter: /^\/secret(\/|$)/, roles: ['admin'] }
  ]
})