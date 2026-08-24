import { useCallback } from 'react';
import { mockGraphQL } from '../graphql/mockClient.js';

export function useProtectedGraphQL(refreshIfNeeded, graphQLClient = mockGraphQL) {
  const executeGraphQL = useCallback(
    async (operationName, variables = {}) => {
      await refreshIfNeeded();
      return graphQLClient(operationName, variables);
    },
    [graphQLClient, refreshIfNeeded]
  );

  return { executeGraphQL };
}
