export function createRouteRegistry() {
  const routes = [];
  const findIndexByName = name => routes.findIndex(route => route.name === name);

  return {
    add(route) {
      if (!route?.name || !route?.path || !route?.element) {
        throw new Error('Route requires name, path, and element');
      }
      if (findIndexByName(route.name) !== -1) {
        throw new Error(`Route already registered: ${route.name}`);
      }
      routes.push(route);
    },
    upsert(route) {
      if (!route?.name || !route?.path || !route?.element) {
        throw new Error('Route requires name, path, and element');
      }
      const index = findIndexByName(route.name);
      if (index === -1) {
        routes.push(route);
      } else {
        routes[index] = route;
      }
    },
    list() {
      return [...routes];
    }
  };
}

export const routeRegistry = createRouteRegistry();
