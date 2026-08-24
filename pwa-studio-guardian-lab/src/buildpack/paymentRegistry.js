export function createPaymentRegistry() {
  const methods = [];

  return {
    add(method) {
      if (!method?.code || !method?.title) {
        throw new Error('Payment method requires code and title');
      }
      if (methods.some(existing => existing.code === method.code)) {
        throw new Error(`Payment method already registered: ${method.code}`);
      }
      methods.push(method);
    },
    list() {
      return [...methods];
    }
  };
}

export const paymentRegistry = createPaymentRegistry();
