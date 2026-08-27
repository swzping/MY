import React from 'react';
import {useReactiveVar} from '@apollo/client';
import {Snackbar} from 'react-native-paper';

import {rxAppSnackbar} from '@app/services/cache';

const SnackbarHost = () => {
  const snackbar = useReactiveVar(rxAppSnackbar);

  return (
    <Snackbar
      visible={Boolean(snackbar)}
      onDismiss={() => rxAppSnackbar(null)}
      duration={2200}>
      {snackbar?.message || ''}
    </Snackbar>
  );
};

export default SnackbarHost;
