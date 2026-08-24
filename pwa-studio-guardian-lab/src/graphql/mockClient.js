import { mockData } from './mockData.js';
import { operations } from './operations.js';

function createTokenPayload(refreshToken) {
  const suffix = String(Date.now()).slice(-5);
  return {
    status: true,
    message: 'refreshed',
    access_token: `access-token-${suffix}`,
    refresh_token: refreshToken || `refresh-token-${suffix}`,
    expires_in: 3600,
    customer_token: {
      token: `customer-token-${suffix}`
    }
  };
}

export async function mockGraphQL(operationName, variables = {}) {
  await new Promise(resolve => setTimeout(resolve, 80));

  switch (operationName) {
    case operations.getProducts:
      return { ok: true, data: { products: mockData.products } };
    case operations.getCustomerDashboard:
      return {
        ok: true,
        data: {
          customer: mockData.customer,
          orders: mockData.orders,
          coupons: mockData.coupons
        }
      };
    case operations.getBusinessModules:
      return {
        ok: true,
        data: {
          healthRecords: mockData.healthRecords,
          events: mockData.events
        }
      };
    case operations.refreshCustomerAccessToken:
      return {
        ok: true,
        data: {
          refreshCustomerAccessToken: createTokenPayload(variables.refresh_token)
        }
      };
    default:
      return {
        ok: false,
        error: { message: `Unknown mock operation: ${operationName}` }
      };
  }
}
