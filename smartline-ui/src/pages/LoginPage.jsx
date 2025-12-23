import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Mail, Lock, ArrowRight } from 'lucide-react';
import Button from '../components/ui/Button';
import Input from '../components/ui/Input';
import Card from '../components/ui/Card';

const LoginPage = () => {
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  
  const handleBypassLogin = () => {
    // TODO: Add actual authentication later
    // For now, just navigate to dashboard
    navigate('/dashboard');
  };
  
  const handleSubmit = (e) => {
    e.preventDefault();
    handleBypassLogin();
  };
  
  return (
    <div className="min-h-screen bg-dark-950 flex items-center justify-center px-4">
      {/* Background Gradient */}
      <div className="absolute inset-0 bg-gradient-to-br from-primary-500/5 via-transparent to-violet-500/5" />
      
      <div className="relative w-full max-w-md animate-fade-in">
        {/* Logo */}
        <div className="text-center mb-8">
          <Link to="/" className="inline-flex items-center gap-2 mb-4">
            <div className="w-12 h-12 bg-gradient-primary rounded-xl flex items-center justify-center">
              <span className="text-white font-bold text-2xl">SL</span>
            </div>
          </Link>
          <h1 className="text-3xl font-display font-bold text-white mb-2">
            Welcome Back
          </h1>
          <p className="text-slate-400">
            Sign in to your SmartLine account
          </p>
        </div>
        
        <Card variant="elevated" padding="lg" glow>
          <form onSubmit={handleSubmit} className="space-y-6">
            <Input
              label="Email"
              type="email"
              placeholder="you@example.com"
              icon={Mail}
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
            
            <Input
              label="Password"
              type="password"
              placeholder="••••••••"
              icon={Lock}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
            
            <div className="flex items-center justify-between text-sm">
              <label className="flex items-center gap-2 text-slate-400 cursor-pointer">
                <input 
                  type="checkbox" 
                  className="w-4 h-4 rounded border-dark-700 bg-dark-900 text-primary-500 focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 focus:ring-offset-dark-950"
                />
                Remember me
              </label>
              <a href="#" className="text-primary-400 hover:text-primary-300 transition-colors">
                Forgot password?
              </a>
            </div>
            
            <Button 
              type="submit" 
              variant="primary" 
              size="lg" 
              className="w-full"
            >
              Sign In
              <ArrowRight className="w-5 h-5 ml-2" />
            </Button>
            
            {/* Bypass Button (Development) */}
            <Button 
              type="button"
              variant="ghost" 
              size="md" 
              className="w-full text-slate-500 hover:text-slate-300"
              onClick={handleBypassLogin}
            >
              Quick Login (Bypass Auth)
            </Button>
          </form>
          
          <div className="mt-6 pt-6 border-t border-dark-700 text-center text-sm">
            <span className="text-slate-400">Don't have an account? </span>
            <Link to="/signup" className="text-primary-400 hover:text-primary-300 transition-colors font-medium">
              Sign up
            </Link>
          </div>
        </Card>
        
        {/* Back to Home */}
        <div className="mt-6 text-center">
          <Link 
            to="/" 
            className="text-slate-400 hover:text-white transition-colors text-sm inline-flex items-center gap-1"
          >
            ← Back to home
          </Link>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;
