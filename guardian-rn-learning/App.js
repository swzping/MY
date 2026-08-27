import React from 'react';
import {ApolloProvider} from '@apollo/client';
import {Provider as PaperProvider} from 'react-native-paper';
import {GestureHandlerRootView} from 'react-native-gesture-handler';

import AppNavigator from '@app/navigation/AppNavigator';
import {client} from '@app/services/mockGraphql';
import {theme} from '@app/styles/theme';

const App = () => {
  return (
    <GestureHandlerRootView style={{flex: 1}}>
      <ApolloProvider client={client}>
        <PaperProvider theme={theme}>
          <AppNavigator />
        </PaperProvider>
      </ApolloProvider>
    </GestureHandlerRootView>
  );
};

export default App;
