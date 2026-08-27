import {modules as coreModules, tabsApp} from '../../core/config/modules';

export const modules = {
  ...coreModules,
  home: {...coreModules.home, label: 'Guardian Lab'},
  scanner: {...coreModules.scanner, label: 'Scan Lab'},
};

export {tabsApp};
