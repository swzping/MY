import { useMemo, useState } from 'react';

export function useCart() {
  const [items, setItems] = useState([]);

  const addItem = product => {
    setItems(current => [...current, { ...product, quantity: 1 }]);
  };

  const total = useMemo(
    () => items.reduce((sum, item) => sum + item.price * item.quantity, 0),
    [items]
  );

  return { items, addItem, total };
}
