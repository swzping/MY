import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.tsx'
import './index.css'

// 在页面上显示调试信息
const debugDiv = document.createElement('div');
debugDiv.style.cssText = 'position:fixed; top:0; left:0; background:yellow; color:black; z-index:99999; padding:10px; font-size:14px;';
debugDiv.innerHTML = 'Loading...';
document.body.appendChild(debugDiv);

try {
  const rootElement = document.getElementById('root');
  if (!rootElement) {
    debugDiv.innerHTML = 'ERROR: Root element not found!';
    debugDiv.style.background = 'red';
    debugDiv.style.color = 'white';
  } else {
    debugDiv.innerHTML = 'Root found, rendering React...';
    ReactDOM.createRoot(rootElement).render(
      <React.StrictMode>
        <App />
      </React.StrictMode>,
    );
    debugDiv.innerHTML = 'React render called successfully!';
    debugDiv.style.background = 'green';
    debugDiv.style.color = 'white';
    
    // 3秒后隐藏调试信息
    setTimeout(() => {
      debugDiv.style.display = 'none';
    }, 3000);
  }
} catch (err: any) {
  debugDiv.innerHTML = 'ERROR: ' + err.message;
  debugDiv.style.background = 'red';
  debugDiv.style.color = 'white';
  console.error(err);
}
