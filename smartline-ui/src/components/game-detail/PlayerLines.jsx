import { Users, TrendingUp, Award } from 'lucide-react';
import Card from '../ui/Card';
import Badge from '../ui/Badge';

/**
 * PlayerLines - Player prop lines tab (placeholder for future development)
 */
const PlayerLines = ({ gameId }) => {
  
  // Placeholder data structure for when this feature is implemented
  const comingSoonFeatures = [
    {
      icon: Users,
      title: 'Player Props',
      description: 'Passing yards, rushing yards, receiving yards, and more'
    },
    {
      icon: TrendingUp,
      title: 'Line Movement',
      description: 'Track how player prop lines move across different books'
    },
    {
      icon: Award,
      title: 'Player Trends',
      description: 'Historical performance and matchup analysis'
    }
  ];
  
  return (
    <div className="space-y-6">
      {/* Coming Soon Banner */}
      <Card variant="elevated" padding="lg" className="text-center">
        <div className="py-8">
          <div className="w-20 h-20 bg-primary-500/10 rounded-full flex items-center justify-center mx-auto mb-6">
            <Users className="w-10 h-10 text-primary-400" />
          </div>
          
          <h3 className="text-2xl font-display font-bold text-white mb-3">
            Player Lines Coming Soon
          </h3>
          
          <p className="text-slate-400 max-w-md mx-auto mb-6">
            We're working on bringing comprehensive player prop analysis to SmartLine. 
            This feature will include real-time line movement, historical trends, and smart betting recommendations.
          </p>
          
          <Badge variant="primary" size="lg">
            In Development
          </Badge>
        </div>
      </Card>
      
      {/* Features Preview */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {comingSoonFeatures.map((feature, index) => {
          const Icon = feature.icon;
          
          return (
            <Card 
              key={index}
              variant="glass" 
              padding="lg"
              className="text-center"
            >
              <div className="w-16 h-16 bg-dark-800 rounded-full flex items-center justify-center mx-auto mb-4">
                <Icon className="w-8 h-8 text-primary-400" />
              </div>
              
              <h4 className="text-lg font-semibold text-white mb-2">
                {feature.title}
              </h4>
              
              <p className="text-sm text-slate-400">
                {feature.description}
              </p>
            </Card>
          );
        })}
      </div>
      
      {/* What to Expect */}
      <Card variant="elevated" padding="lg">
        <Card.Header>
          <Card.Title>What to Expect</Card.Title>
          <Card.Description>Features we're building for player analysis</Card.Description>
        </Card.Header>
        <Card.Content>
          <ul className="space-y-3">
            <li className="flex items-start gap-3">
              <div className="w-6 h-6 bg-primary-500/10 rounded-full flex items-center justify-center mt-0.5 flex-shrink-0">
                <span className="text-primary-400 text-sm">✓</span>
              </div>
              <div>
                <p className="text-white font-medium">Real-Time Player Props</p>
                <p className="text-sm text-slate-400">
                  Live odds for passing yards, touchdowns, receptions, and more
                </p>
              </div>
            </li>
            
            <li className="flex items-start gap-3">
              <div className="w-6 h-6 bg-primary-500/10 rounded-full flex items-center justify-center mt-0.5 flex-shrink-0">
                <span className="text-primary-400 text-sm">✓</span>
              </div>
              <div>
                <p className="text-white font-medium">Multi-Book Comparison</p>
                <p className="text-sm text-slate-400">
                  Find the best available lines across all major sportsbooks
                </p>
              </div>
            </li>
            
            <li className="flex items-start gap-3">
              <div className="w-6 h-6 bg-primary-500/10 rounded-full flex items-center justify-center mt-0.5 flex-shrink-0">
                <span className="text-primary-400 text-sm">✓</span>
              </div>
              <div>
                <p className="text-white font-medium">Performance Trends</p>
                <p className="text-sm text-slate-400">
                  Historical stats, matchup data, and weather impact on player performance
                </p>
              </div>
            </li>
            
            <li className="flex items-start gap-3">
              <div className="w-6 h-6 bg-primary-500/10 rounded-full flex items-center justify-center mt-0.5 flex-shrink-0">
                <span className="text-primary-400 text-sm">✓</span>
              </div>
              <div>
                <p className="text-white font-medium">Smart Alerts</p>
                <p className="text-sm text-slate-400">
                  Get notified when player prop lines move significantly
                </p>
              </div>
            </li>
          </ul>
        </Card.Content>
      </Card>
    </div>
  );
};

export default PlayerLines;
