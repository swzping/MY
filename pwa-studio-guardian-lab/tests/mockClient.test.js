import { describe, expect, it } from 'vitest';
import { mockGraphQL } from '../src/graphql/mockClient.js';

describe('mockGraphQL', () => {
  it('returns products for GetProducts', async () => {
    const result = await mockGraphQL('GetProducts');
    expect(result.ok).toBe(true);
    expect(result.data.products.length).toBeGreaterThan(1);
  });

  it('returns token refresh payload', async () => {
    const result = await mockGraphQL('RefreshCustomerAccessToken', {
      refresh_token: 'refresh-demo'
    });
    expect(result.ok).toBe(true);
    expect(result.data.refreshCustomerAccessToken.customer_token.token).toContain(
      'customer-token'
    );
  });

  it('returns structured errors for unknown operations', async () => {
    const result = await mockGraphQL('UnknownOperation');
    expect(result.ok).toBe(false);
    expect(result.error.message).toBe('Unknown mock operation: UnknownOperation');
  });
});
