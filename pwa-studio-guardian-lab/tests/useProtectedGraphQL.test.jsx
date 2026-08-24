import { act, renderHook } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { operations } from '../src/graphql/operations.js';
import { useProtectedGraphQL } from '../src/talons/useProtectedGraphQL.js';

describe('useProtectedGraphQL', () => {
  it('refreshes auth before executing protected GraphQL operations', async () => {
    const calls = [];
    const refreshIfNeeded = vi.fn(async () => {
      calls.push('refresh');
    });
    const graphQLClient = vi.fn(async operationName => {
      calls.push(operationName);
      return { ok: true, data: { products: [] } };
    });

    const { result } = renderHook(() =>
      useProtectedGraphQL(refreshIfNeeded, graphQLClient)
    );

    await act(async () => {
      await result.current.executeGraphQL(operations.getProducts);
    });

    expect(calls).toEqual(['refresh', operations.getProducts]);
    expect(refreshIfNeeded).toHaveBeenCalledTimes(1);
    expect(graphQLClient).toHaveBeenCalledWith(operations.getProducts, {});
  });
});
