import { Link } from 'react-router-dom';
import { 
  TrendingUp, 
  BarChart3, 
  Zap, 
  Shield,
  ArrowRight,
  CheckCircle2
} from 'lucide-react';
import Button from '../components/ui/Button';
import Card from '../components/ui/Card';
import Badge from '../components/ui/Badge';

const LandingPage = () => {
  return (
    <div className="min-h-screen bg-dark-950">
      
      {/* Navigation */}
      <nav className="border-b border-dark-700 bg-dark-950/95 backdrop-blur-sm sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 bg-gradient-primary rounded-lg flex items-center justify-center">
                <span className="text-white font-bold text-lg">SL</span>
              </div>
              <span className="font-display font-bold text-xl text-white">
                SmartLine
              </span>
            </div>
            
            <Link to="/login">
              <Button variant="primary" size="md">
                Get Started
              </Button>
            </Link>
          </div>
        </div>
      </nav>
      
      {/* Hero Section */}
      <section className="relative overflow-hidden">
        {/* Background Gradient */}
        <div className="absolute inset-0 bg-gradient-to-br from-primary-500/10 via-transparent to-violet-500/10" />
        
        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20 sm:py-32">
          <div className="text-center animate-fade-in">
            <Badge variant="primary" size="md" className="mb-6">
              <Zap className="w-3 h-3 mr-1" />
              NFL Betting Analytics Platform
            </Badge>
            
            <h1 className="text-4xl sm:text-5xl md:text-6xl lg:text-7xl font-display font-bold text-white mb-6 leading-tight">
              Make Smarter Bets with
              <br />
              <span className="bg-gradient-primary bg-clip-text text-transparent">
                Data-Driven Insights
              </span>
            </h1>
            
            <p className="text-lg sm:text-xl text-slate-400 max-w-3xl mx-auto mb-10">
              Track NFL odds in real-time, analyze line movements, and make informed betting 
              decisions with comprehensive data and advanced analytics.
            </p>
            
            <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
              <Link to="/login">
                <Button variant="primary" size="lg" className="w-full sm:w-auto">
                  Start Analyzing
                  <ArrowRight className="w-5 h-5 ml-2" />
                </Button>
              </Link>
              <Button variant="outline" size="lg" className="w-full sm:w-auto">
                View Demo
              </Button>
            </div>
          </div>
        </div>
      </section>
      
      {/* Features Section */}
      <section className="py-20 bg-gradient-dark">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl sm:text-4xl font-display font-bold text-white mb-4">
              Everything You Need to Win
            </h2>
            <p className="text-lg text-slate-400 max-w-2xl mx-auto">
              Powerful tools and real-time data to give you the edge in NFL betting
            </p>
          </div>
          
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6 animate-slide-up">
            {/* Feature 1 */}
            <Card variant="glass" hover glow className="group">
              <div className="w-12 h-12 bg-primary-500/10 rounded-lg flex items-center justify-center mb-4 group-hover:bg-primary-500/20 transition-colors">
                <TrendingUp className="w-6 h-6 text-primary-400" />
              </div>
              <Card.Title>Real-Time Odds</Card.Title>
              <Card.Description>
                Track opening and closing lines from multiple sportsbooks with live updates
              </Card.Description>
            </Card>
            
            {/* Feature 2 */}
            <Card variant="glass" hover glow className="group">
              <div className="w-12 h-12 bg-violet-500/10 rounded-lg flex items-center justify-center mb-4 group-hover:bg-violet-500/20 transition-colors">
                <BarChart3 className="w-6 h-6 text-violet-400" />
              </div>
              <Card.Title>Line Movement Analysis</Card.Title>
              <Card.Description>
                Visualize how lines move and identify sharp money patterns
              </Card.Description>
            </Card>
            
            {/* Feature 3 */}
            <Card variant="glass" hover glow className="group">
              <div className="w-12 h-12 bg-emerald-500/10 rounded-lg flex items-center justify-center mb-4 group-hover:bg-emerald-500/20 transition-colors">
                <Shield className="w-6 h-6 text-emerald-400" />
              </div>
              <Card.Title>Historical Data</Card.Title>
              <Card.Description>
                Access comprehensive 2023 season data with opening and closing lines
              </Card.Description>
            </Card>
            
            {/* Feature 4 */}
            <Card variant="glass" hover glow className="group">
              <div className="w-12 h-12 bg-amber-500/10 rounded-lg flex items-center justify-center mb-4 group-hover:bg-amber-500/20 transition-colors">
                <CheckCircle2 className="w-6 h-6 text-amber-400" />
              </div>
              <Card.Title>Multi-Book Comparison</Card.Title>
              <Card.Description>
                Compare odds across DraftKings, FanDuel, BetMGM, and Caesars
              </Card.Description>
            </Card>
            
            {/* Feature 5 */}
            <Card variant="glass" hover glow className="group">
              <div className="w-12 h-12 bg-red-500/10 rounded-lg flex items-center justify-center mb-4 group-hover:bg-red-500/20 transition-colors">
                <Zap className="w-6 h-6 text-red-400" />
              </div>
              <Card.Title>Advanced Analytics</Card.Title>
              <Card.Description>
                Get insights on trends, team performance, and betting patterns
              </Card.Description>
            </Card>
            
            {/* Feature 6 */}
            <Card variant="glass" hover glow className="group">
              <div className="w-12 h-12 bg-blue-500/10 rounded-lg flex items-center justify-center mb-4 group-hover:bg-blue-500/20 transition-colors">
                <TrendingUp className="w-6 h-6 text-blue-400" />
              </div>
              <Card.Title>Clean Dashboard</Card.Title>
              <Card.Description>
                Modern, intuitive interface designed for quick decision-making
              </Card.Description>
            </Card>
          </div>
        </div>
      </section>
      
      {/* CTA Section */}
      <section className="py-20">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <Card variant="elevated" padding="lg" glow>
            <h2 className="text-3xl sm:text-4xl font-display font-bold text-white mb-4">
              Ready to Start Winning?
            </h2>
            <p className="text-lg text-slate-400 mb-8">
              Join SmartLine today and get access to professional-grade NFL betting analytics
            </p>
            <Link to="/login">
              <Button variant="primary" size="xl">
                Get Started Now
                <ArrowRight className="w-5 h-5 ml-2" />
              </Button>
            </Link>
          </Card>
        </div>
      </section>
      
      {/* Footer */}
      <footer className="border-t border-dark-700 py-8">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-2">
              <div className="w-6 h-6 bg-gradient-primary rounded-md flex items-center justify-center">
                <span className="text-white font-bold text-sm">SL</span>
              </div>
              <span className="text-slate-400 text-sm">
                © 2026 SmartLine. All rights reserved.
              </span>
            </div>
            <div className="flex items-center gap-6 text-sm text-slate-400">
              <a href="#" className="hover:text-white transition-colors">Privacy</a>
              <a href="#" className="hover:text-white transition-colors">Terms</a>
              <a href="#" className="hover:text-white transition-colors">Contact</a>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default LandingPage;
