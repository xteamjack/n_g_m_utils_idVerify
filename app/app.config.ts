export default defineAppConfig({
  authRoutes: [
    { routeFilter: /^\/apps(\/|$)/, roles: [] },
    { routeFilter: /^\/secret(\/|$)/, roles: ['admin'] }
  ]
})
