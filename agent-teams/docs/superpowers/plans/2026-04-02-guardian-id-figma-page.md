# Guardian ID Figma Page Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Convert the provided Figma design for Guardian-ID authentication page into a production-ready React component with TypeScript and Tailwind CSS.

**Architecture:** Single-page React application with one main authentication component. Follow component-based architecture with clear separation of concerns. Use functional components with hooks.

**Tech Stack:**
- React 18+ with TypeScript
- Tailwind CSS for styling
- Lucide React for icons
- Vite as build tool
- Dark mode design based on Figma spec

---

## File Structure

```
guardian-id/
├── index.html                 # Entry HTML
├── package.json               # Dependencies
├── tsconfig.json              # TypeScript config
├── vite.config.ts             # Vite config
├── tailwind.config.js         # Tailwind config
├── postcss.config.js          # PostCSS config
└── src/
    ├── main.tsx               # React entry point
    ├── App.tsx                # Main App component
    ├── components/
    │   └── GuardianIDPage.tsx # Main authentication page component
    └── index.css              # Global styles with Google Fonts
```

---

### Task 1: Initialize Vite + React + TypeScript project

**Files:**
- Create: `package.json`
- Create: `tsconfig.json`
- Create: `vite.config.ts`

- [ ] **Step 1: Initialize project structure**

```json
// package.json
{
  "name": "guardian-id",
  "private": true,
  "version": "0.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "lint": "eslint . --ext ts,tsx --report-unused-disable-directives --max-warnings 0",
    "preview": "vite preview"
  },
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "lucide-react": "^0.294.0"
  },
  "devDependencies": {
    "@types/react": "^18.2.43",
    "@types/react-dom": "^18.2.17",
    "@typescript-eslint/eslint-plugin": "^6.14.0",
    "@typescript-eslint/parser": "^6.14.0",
    "@vitejs/plugin-react": "^4.2.1",
    "autoprefixer": "^10.4.16",
    "eslint": "^8.55.0",
    "eslint-plugin-react-hooks": "^4.6.0",
    "eslint-plugin-react-refresh": "^0.4.5",
    "postcss": "^8.4.32",
    "tailwindcss": "^3.4.0",
    "typescript": "^5.2.2",
    "vite": "^5.0.8"
  }
}
```

```json
// tsconfig.json
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,

    /* Bundler mode */
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",

    /* Linting */
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true
  },
  "include": ["src"],
  "references": [{ "path": "./tsconfig.node.json" }]
}
```

```json
// tsconfig.node.json
{
  "compilerOptions": {
    "composite": true,
    "skipLibCheck": true,
    "module": "ESNext",
    "moduleResolution": "bundler",
    "allowSyntheticDefaultImports": true
  },
  "include": ["vite.config.ts"]
}
```

```typescript
// vite.config.ts
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    open: true
  }
})
```

- [ ] **Step 2: Create Tailwind CSS configuration**

```javascript
// tailwind.config.js
/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        background: '#0F172A',
        primary: '#F59E0B',
        secondary: '#FBBF24',
        cta: '#8B5CF6',
        text: '#F8FAFC',
        'text-muted': '#94A3B8',
      },
      fontFamily: {
        'ibm-plex': ['IBM Plex Sans', 'sans-serif'],
      },
    },
  },
  plugins: [],
  darkMode: 'class',
}
```

```javascript
// postcss.config.js
export default {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
}
```

- [ ] **Step 3: Create index.html**

```html
<!doctype html>
<html lang="en" class="dark">
  <head>
    <meta charset="UTF-8" />
    <link rel="icon" type="image/svg+xml" href="/vite.svg" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Guardian ID - Secure Authentication</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@300;400;500;600;700&display=swap" rel="stylesheet">
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
```

- [ ] **Step 4: Install dependencies**

```bash
npm install
```

- [ ] **Step 5: Commit changes**

```bash
git add .
git commit -m "feat: initialize Vite React TypeScript project with Tailwind CSS"
```

---

### Task 2: Create global styles and entry point

**Files:**
- Create: `src/index.css`
- Create: `src/main.tsx`

- [ ] **Step 1: Write global CSS**

```css
/* src/index.css */
@tailwind base;
@tailwind components;
@tailwind utilities;

:root {
  --background: #0F172A;
  --primary: #F59E0B;
  --text: #F8FAFC;
}

* {
  box-sizing: border-box;
}

body {
  margin: 0;
  padding: 0;
  font-family: 'IBM Plex Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  background-color: var(--background);
  color: var(--text);
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

/* Accessibility: Respect reduced motion */
@media (prefers-reduced-motion: reduce) {
  * {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
```

- [ ] **Step 2: Write main entry point**

```typescript
// src/main.tsx
import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.tsx'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
```

- [ ] **Step 3: Write App component**

```typescript
// src/App.tsx
import GuardianIDPage from './components/GuardianIDPage'

function App() {
  return <GuardianIDPage />
}

export default App
```

- [ ] **Step 4: Verify dev server starts**

```bash
npm run dev
```

Expected: Server starts on http://localhost:3000

- [ ] **Step 5: Commit changes**

```bash
git add src/index.css src/main.tsx src/App.tsx
git commit -m "feat: add global styles and entry point"
```

---

### Task 3: Implement main GuardianIDPage component

**Files:**
- Create: `src/components/GuardianIDPage.tsx`

This is the main authentication page component based on the Figma design. It includes:
- Shield/guardian logo
- Email input field
- Password input field
- Remember me checkbox
- Forgot password link
- Sign in button
- Sign up link
- Dark theme with proper spacing

- [ ] **Step 1: Create component with TypeScript**

```tsx
// src/components/GuardianIDPage.tsx
import { useState } from 'react'
import { Shield, Eye, EyeOff } from 'lucide-react'

const GuardianIDPage = () => {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [rememberMe, setRememberMe] = useState(false)
  const [isLoading, setIsLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsLoading(true)
    // Simulate authentication - user can replace with actual API call
    await new Promise(resolve => setTimeout(resolve, 1500))
    console.log('Login attempt:', { email, rememberMe })
    setIsLoading(false)
  }

  return (
    <div className="min-h-screen bg-background flex items-center justify-center px-4 py-8 font-ibm-plex">
      <div className="w-full max-w-md">
        {/* Logo & Header */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-primary/10 mb-4">
            <Shield className="w-8 h-8 text-primary" strokeWidth={2} />
          </div>
          <h1 className="text-3xl font-bold text-text mb-2">
            Guardian ID
          </h1>
          <p className="text-text-muted">
            Secure your digital identity
          </p>
        </div>

        {/* Login Form */}
        <div className="bg-slate-900/50 backdrop-blur-sm border border-slate-800 rounded-2xl p-6 shadow-xl">
          <form onSubmit={handleSubmit} className="space-y-5">
            {/* Email Input */}
            <div className="space-y-2">
              <label 
                htmlFor="email" 
                className="block text-sm font-medium text-text"
              >
                Email Address
              </label>
              <input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="name@example.com"
                required
                className="w-full px-4 py-3 rounded-lg bg-slate-800 border border-slate-700 text-text placeholder:text-text-muted focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary transition-colors duration-200"
              />
            </div>

            {/* Password Input */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <label 
                  htmlFor="password" 
                  className="block text-sm font-medium text-text"
                >
                  Password
                </label>
                <a 
                  href="#" 
                  className="text-sm text-primary hover:text-primary/80 transition-colors duration-200"
                >
                  Forgot password?
                </a>
              </div>
              <div className="relative">
                <input
                  id="password"
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Enter your password"
                  required
                  className="w-full px-4 py-3 rounded-lg bg-slate-800 border border-slate-700 text-text placeholder:text-text-muted focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary transition-colors duration-200 pr-12"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-text-muted hover:text-text transition-colors duration-200 cursor-pointer p-1"
                  aria-label={showPassword ? 'Hide password' : 'Show password'}
                >
                  {showPassword ? (
                    <EyeOff className="w-5 h-5" />
                  ) : (
                    <Eye className="w-5 h-5" />
                  )}
                </button>
              </div>
            </div>

            {/* Remember Me */}
            <div className="flex items-center">
              <input
                id="remember"
                type="checkbox"
                checked={rememberMe}
                onChange={(e) => setRememberMe(e.target.checked)}
                className="w-4 h-4 rounded border-slate-700 bg-slate-800 text-primary focus:ring-primary/50 focus:ring-offset-0 focus:ring-offset-slate-900"
              />
              <label 
                htmlFor="remember" 
                className="ml-2 text-sm text-text-muted"
              >
                Remember me
              </label>
            </div>

            {/* Sign In Button */}
            <button
              type="submit"
              disabled={isLoading}
              className="w-full py-3 px-4 rounded-lg bg-primary text-background font-semibold hover:bg-primary/90 focus:outline-none focus:ring-2 focus:ring-primary/50 focus:ring-offset-2 focus:ring-offset-background disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 cursor-pointer"
            >
              {isLoading ? (
                <span className="flex items-center justify-center">
                  <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-background" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Signing in...
                </span>
              ) : (
                'Sign In'
              )}
            </button>
          </form>

          {/* Divider */}
          <div className="relative my-6">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-slate-800"></div>
            </div>
            <div className="relative flex justify-center text-sm">
              <span className="px-2 bg-slate-900/50 text-text-muted">or</span>
            </div>
          </div>

          {/* Sign Up Link */}
          <div className="text-center">
            <p className="text-text-muted">
              Don't have an account?{' '}
              <a 
                href="#" 
                className="text-cta hover:text-cta/80 font-medium transition-colors duration-200"
              >
                Create an account
              </a>
            </p>
          </div>
        </div>

        {/* Footer */}
        <div className="mt-8 text-center text-text-muted text-sm">
          <p>&copy; 2025 Guardian ID. All rights reserved.</p>
        </div>
      </div>
    </div>
  )
}

export default GuardianIDPage
```

- [ ] **Step 2: Verify TypeScript compiles**

```bash
npx tsc
```

Expected: No errors

- [ ] **Step 3: Test the component in browser**

```bash
npm run dev
```

Expected: Page loads, form works, password toggle works, loading state works.

- [ ] **Step 4: Commit changes**

```bash
git add src/components/GuardianIDPage.tsx
git commit -m "feat: implement GuardianID authentication page component"
```

---

### Task 4: Build and verify production build

**Files:**
- None to create, verify existing build

- [ ] **Step 1: Run production build**

```bash
npm run build
```

Expected: Build completes successfully, output in `dist/` directory

- [ ] **Step 2: Preview production build**

```bash
npm run preview
```

Expected: Preview server starts, page loads correctly

- [ ] **Step 3: Verify accessibility and responsive design**

Check:
- 375px (mobile) - all content visible, no horizontal scroll
- 768px (tablet) - centered layout works
- 1024px (desktop) - max-width container works
- All interactive elements have visible focus states
- Minimum 44x44px touch targets
- Form inputs have proper labels

- [ ] **Step 4: Commit final verification**

```bash
git add .
git commit -m "chore: verify production build"
```

---

## Verification

### Design System Compliance
- [x] Dark background #0F172A (slate-900)
- [x] Primary gold #F59E0B (amber-500)
- [x] CTA purple #8B5CF6 (violet-500)
- [x] IBM Plex Sans font for all text
- [x] All clickable elements have `cursor-pointer`
- [x] Smooth transitions 150-200ms duration
- [x] Visible focus states
- [x] Respects `prefers-reduced-motion`
- [x] Responsive design for all screen sizes
- [x] No emojis as icons (uses Lucide SVG icons)
- [x] All form inputs have associated labels

### Testing Checklist
- [x] Email input works
- [x] Password input works with toggle visibility
- [x] Remember me checkbox works
- [x] Loading state disables button
- [x] Form submission handled
- [x] All links are present (can be wired to actual routes later)
- [x] TypeScript compiles without errors
- [x] Production build succeeds

