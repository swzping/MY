import { Eye, EyeOff, Facebook } from 'lucide-react';
import { useState } from 'react';

export default function GuardianIDLoginPage() {
  const [showPassword, setShowPassword] = useState(false);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [rememberMe, setRememberMe] = useState(false);

  return (
    <div className="min-h-screen bg-[#FF7A00] font-sans flex items-center justify-center p-4">
      <div className="w-full max-w-md bg-white rounded-2xl shadow-xl p-8">
        {/* Logo */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold italic text-[#FF7A00] mb-2">guardian</h1>
          <h2 className="text-xl font-bold text-gray-900">Guardian ID</h2>
          <p className="text-gray-500 text-sm mt-1">Sign in to your account</p>
        </div>

        {/* Login Form */}
        <form className="space-y-4" onSubmit={(e) => e.preventDefault()}>
          {/* Email */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Email Address *</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="Enter your email"
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#FF7A00] focus:border-transparent text-sm"
            />
          </div>

          {/* Password */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Password *</label>
            <div className="relative">
              <input
                type={showPassword ? 'text' : 'password'}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Enter your password"
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#FF7A00] focus:border-transparent text-sm pr-12"
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
              >
                {showPassword ? <EyeOff size={20} /> : <Eye size={20} />}
              </button>
            </div>
          </div>

          {/* Remember Me & Forgot Password */}
          <div className="flex items-center justify-between">
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={rememberMe}
                onChange={(e) => setRememberMe(e.target.checked)}
                className="w-4 h-4 text-[#FF7A00] focus:ring-[#FF7A00] border-gray-300 rounded"
              />
              <span className="text-sm text-gray-700">Remember me</span>
            </label>
            <a href="#" className="text-sm text-[#FF7A00] hover:underline">Forgot Password?</a>
          </div>

          {/* Sign In Button */}
          <button
            type="submit"
            className="w-full py-3 bg-[#FF7A00] hover:bg-[#e66e00] text-white font-semibold rounded-lg transition-colors"
          >
            Sign In
          </button>

          {/* Divider */}
          <div className="relative my-6">
            <div className="absolute inset-0 flex items-center">
              <hr className="w-full border-gray-200" />
            </div>
            <div className="relative flex justify-center text-sm">
              <span className="px-4 bg-white text-gray-500">or continue with</span>
            </div>
          </div>

          {/* Social Login */}
          <div className="grid grid-cols-2 gap-3">
            <button
              type="button"
              className="flex items-center justify-center gap-2 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
            >
              <svg className="w-5 h-5" viewBox="0 0 24 24">
                <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                <path fill="#FBBC05" d="M5.84 14.09c-.26-.78-.26-1.6 0-2.38V8.87H2.18c-.65 1.38-1 2.94-1 4.63s.35 3.25 1 4.63l3.66-2.85z"/>
                <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 0 12 0 7.7 0 3.99 2.47 2.18 6.35l3.66 2.85c.87-2.6 3.3-4.53 6.16-4.53z"/>
              </svg>
              <span className="text-sm font-medium">Google</span>
            </button>
            <button
              type="button"
              className="flex items-center justify-center gap-2 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
            >
              <Facebook size={20} className="text-blue-600" />
              <span className="text-sm font-medium">Facebook</span>
            </button>
          </div>

          {/* Sign Up Link */}
          <div className="text-center pt-4">
            <p className="text-sm text-gray-600">
              Don't have an account?{' '}
              <a href="/node-2179-516518" className="font-semibold text-[#FF7A00] hover:underline">
                Sign Up
              </a>
            </p>
          </div>
        </form>

        {/* Terms */}
        <div className="mt-6 text-xs text-center text-gray-500">
          <p>
            By signing in, you agree to our{' '}
            <a href="#" className="text-[#FF7A00] underline">Terms of Service</a>
            {' '}and{' '}
            <a href="#" className="text-[#FF7A00] underline">Privacy Policy</a>
          </p>
        </div>
      </div>
    </div>
  );
}
