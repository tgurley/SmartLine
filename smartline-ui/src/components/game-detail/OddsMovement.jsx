import { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { TrendingUp, TrendingDown, ArrowRight } from 'lucide-react';
import Card from '../ui/Card';
import Badge from '../ui/Badge';
import { cn } from '../../lib/utils';

/**
 * OddsMovement - Displays line movement and book comparison
 */
const OddsMovement = ({ gameId, game }) => {
  const [oddsData, setOddsData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selectedMarket, setSelectedMarket] = useState('spread');
  
  useEffect(() => {
    const fetchOdds = async () => {
      setLoading(true);
      try {
        const apiUrl = import.meta.env.VITE_API_URL || 'https://smartline-production.up.railway.app';
        const response = await fetch(`${apiUrl}/odds/game/${gameId}`);
        
        if (response.ok) {
          const data = await response.json();
          setOddsData(data);
        }
      } catch (err) {
        console.error('Error fetching odds:', err);
      } finally {
        setLoading(false);
      }
    };
    
    fetchOdds();
  }, [gameId]);
  
  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-primary-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-slate-400">Loading odds data...</p>
        </div>
      </div>
    );
  }
  
  if (!oddsData || !oddsData.books) {
    return (
      <Card variant="elevated" padding="lg">
        <div className="text-center py-12">
          <p className="text-slate-400 mb-4">No odds data available for this game</p>
          <p className="text-sm text-slate-500">Check back closer to game time</p>
        </div>
      </Card>
    );
  }
  
  // Prepare line movement data for chart
  const prepareLineMovement = () => {
    const books = Object.keys(oddsData.books);
    if (books.length === 0) return [];
    
    const firstBook = oddsData.books[books[0]];
    const marketData = firstBook[selectedMarket] || [];
    
    return marketData.map((entry, index) => ({
      timestamp: new Date(entry.pulled_at).toLocaleTimeString('en-US', { 
        hour: 'numeric', 
        minute: '2-digit' 
      }),
      line: entry.line,
      index
    }));
  };
  
  const lineMovement = prepareLineMovement();
  
  // Calculate consensus and best lines
  const calculateConsensus = () => {
    const books = Object.keys(oddsData.books);
    const latestLines = books.map(book => {
      const marketData = oddsData.books[book][selectedMarket];
      if (!marketData || marketData.length === 0) return null;
      return marketData[marketData.length - 1];
    }).filter(Boolean);
    
    if (latestLines.length === 0) return null;
    
    const avgLine = latestLines.reduce((sum, line) => sum + parseFloat(line.line), 0) / latestLines.length;
    const bestLine = latestLines.reduce((best, current) => {
      return Math.abs(parseFloat(current.line)) < Math.abs(parseFloat(best.line)) ? current : best;
    });
    
    return { avgLine: avgLine.toFixed(1), bestLine };
  };
  
  const consensus = calculateConsensus();
  
  return (
    <div className="space-y-6">
      {/* Market Selector */}
      <div className="flex gap-3">
        {['spread', 'total', 'moneyline'].map((market) => (
          <button
            key={market}
            onClick={() => setSelectedMarket(market)}
            className={cn(
              "px-4 py-2 rounded-lg font-medium transition-all capitalize",
              selectedMarket === market
                ? "bg-primary-500 text-white"
                : "bg-dark-800 text-slate-400 hover:text-white"
            )}
          >
            {market}
          </button>
        ))}
      </div>
      
      {/* Consensus & Best Line */}
      {consensus && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Card variant="glass" padding="md">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm text-slate-400 mb-1">Consensus Line</p>
                <p className="text-3xl font-display font-bold text-white">
                  {selectedMarket === 'spread' && game.home_team.abbrev + ' '}
                  {consensus.avgLine}
                </p>
              </div>
              <TrendingUp className="w-8 h-8 text-primary-400" />
            </div>
          </Card>
          
          <Card variant="glass" padding="md">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm text-slate-400 mb-1">Best Available</p>
                <p className="text-3xl font-display font-bold text-emerald-400">
                  {selectedMarket === 'spread' && game.home_team.abbrev + ' '}
                  {consensus.bestLine.line}
                </p>
              </div>
              <Badge variant="success" size="sm">Best</Badge>
            </div>
          </Card>
        </div>
      )}
      
      {/* Line Movement Chart */}
      {lineMovement.length > 1 && (
        <Card variant="elevated" padding="lg">
          <Card.Header>
            <Card.Title>Line Movement</Card.Title>
            <Card.Description>
              {selectedMarket.charAt(0).toUpperCase() + selectedMarket.slice(1)} line movement over time
            </Card.Description>
          </Card.Header>
          <Card.Content>
            <div className="h-80">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={lineMovement}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                  <XAxis 
                    dataKey="timestamp" 
                    stroke="#94a3b8"
                    tick={{ fill: '#94a3b8' }}
                  />
                  <YAxis 
                    stroke="#94a3b8"
                    tick={{ fill: '#94a3b8' }}
                  />
                  <Tooltip 
                    contentStyle={{ 
                      backgroundColor: '#1e293b', 
                      border: '1px solid #475569',
                      borderRadius: '8px'
                    }}
                  />
                  <Legend />
                  <Line 
                    type="monotone" 
                    dataKey="line" 
                    stroke="#0ea5e9" 
                    strokeWidth={2}
                    dot={{ fill: '#0ea5e9', r: 4 }}
                    name={selectedMarket.charAt(0).toUpperCase() + selectedMarket.slice(1)}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </Card.Content>
        </Card>
      )}
      
      {/* Book Comparison Table */}
      <Card variant="elevated" padding="lg">
        <Card.Header>
          <Card.Title>Sportsbook Comparison</Card.Title>
          <Card.Description>Compare current lines across all books</Card.Description>
        </Card.Header>
        <Card.Content>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-dark-700">
                  <th className="text-left py-3 px-4 text-sm font-semibold text-slate-400">Book</th>
                  <th className="text-center py-3 px-4 text-sm font-semibold text-slate-400">Opening</th>
                  <th className="text-center py-3 px-4 text-sm font-semibold text-slate-400">Current</th>
                  <th className="text-center py-3 px-4 text-sm font-semibold text-slate-400">Movement</th>
                  <th className="text-right py-3 px-4 text-sm font-semibold text-slate-400">Price</th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(oddsData.books).map(([bookName, markets]) => {
                  const marketData = markets[selectedMarket];
                  if (!marketData || marketData.length === 0) return null;
                  
                  const opening = marketData[0];
                  const current = marketData[marketData.length - 1];
                  const movement = parseFloat(current.line) - parseFloat(opening.line);
                  
                  return (
                    <tr key={bookName} className="border-b border-dark-800 hover:bg-dark-800/50 transition-colors">
                      <td className="py-3 px-4 font-medium text-white">{bookName}</td>
                      <td className="py-3 px-4 text-center text-slate-300">
                        {opening.line}
                      </td>
                      <td className="py-3 px-4 text-center font-semibold text-white">
                        {current.line}
                      </td>
                      <td className="py-3 px-4 text-center">
                        {movement !== 0 ? (
                          <span className={cn(
                            "flex items-center justify-center gap-1",
                            movement > 0 ? "text-emerald-400" : "text-red-400"
                          )}>
                            {movement > 0 ? (
                              <TrendingUp className="w-4 h-4" />
                            ) : (
                              <TrendingDown className="w-4 h-4" />
                            )}
                            {Math.abs(movement).toFixed(1)}
                          </span>
                        ) : (
                          <span className="text-slate-500">-</span>
                        )}
                      </td>
                      <td className="py-3 px-4 text-right text-slate-300">
                        {current.price}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </Card.Content>
      </Card>
    </div>
  );
};

export default OddsMovement;
