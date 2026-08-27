import React from 'react';
import {Button} from 'react-native-paper';

const ActionButton = ({children, mode = 'contained', style, ...props}) => (
  <Button mode={mode} compact style={[{borderRadius: 6}, style]} {...props}>
    {children}
  </Button>
);

export default ActionButton;
