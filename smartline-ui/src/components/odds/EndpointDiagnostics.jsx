import { useState } from 'react';
import { CheckCircle, XCircle, AlertCircle, Loader } from 'lucide-react';
import Card from '../ui/Card';
import Badge from '../ui/Badge';
import Button from '../ui/Button';

/**
 * Diagnostic Component - Test Player Odds Endpoints
 * 
 * This component tests all player odds endpoints to verify they're working.
 * Useful for debugging deployment issues.
 * 
 * Usage: Add to your odds dashboard during development
 */

const EndpointDiagnostics = () => {
  const [results, setResults] = useState({});
  const [testing, setTesting] = useState(false);

  const API_BASE = 'https://smartline-production.up.railway.app';

  const endpoints = [
    {
      name: 'Players List',
      url: `${API_BASE}/players`,
      key: 'players'
    },
    {
      name: 'Games with Props',
      url: `${API_BASE}/player-odds/games?season_year=2023&week=1`,
      key: 'games'
    },
    {
      name: 'Player Streaks',
      url: `${API_BASE}/player-odds/streaks?season_year=2023&min_streak_length=3`,
      key: 'streaks'
    },
    {
      name: 'Sharp Movement',
      url: `${API_BASE}/player-odds/sharp-movement?season_year=2023&limit=10`,
      key: 'sharp-movement'
    },
    {
      name: 'Best Odds (Sample)',
      url: `${API_BASE}/player-odds/best-odds?season_year=2023&week=1&limit=5`,
      key: 'best-odds'
    },
    {
      name: 'Bookmakers',
      url: `${API_BASE}/player-odds/bookmakers?season_year=2023`,
      key: 'bookmakers'
    },
    {
      name: 'Home/Away Splits',
      url: `${API_BASE}/player-odds/home-away-splits?season_year=2023&limit=5`,
      key: 'splits'
    },
  ];

  const testEndpoints = async () => {
    setTesting(true);
    setResults({});

    for (const endpoint of endpoints) {
      try {
        const startTime = Date.now();
        const response = await fetch(endpoint.url);
        const responseTime = Date.now() - startTime;
        
        let data;
        try {
          data = await response.json();
        } catch (e) {
          data = null;
        }

        setResults(prev => ({
          ...prev,
          [endpoint.key]: {
            status: response.status,
            ok: response.ok,
            responseTime,
            dataCount: Array.isArray(data) ? data.length : (data ? 1 : 0),
            error: !response.ok ? data?.detail || 'Unknown error' : null
          }
        }));
      } catch (error) {
        setResults(prev => ({
          ...prev,
          [endpoint.key]: {
            status: 0,
            ok: false,
            responseTime: 0,
            dataCount: 0,
            error: error.message
          }
        }));
      }

      // Small delay between requests
      await new Promise(resolve => setTimeout(resolve, 200));
    }

    setTesting(false);
  };

  const getStatusIcon = (result) => {
    if (!result) return <AlertCircle className="w-5 h-5 text-slate-500" />;
    if (result.ok) return <CheckCircle className="w-5 h-5 text-emerald-400" />;
    return <XCircle className="w-5 h-5 text-red-400" />;
  };

  const getStatusBadge = (result) => {
    if (!result) return <Badge variant="default" size="sm">Not tested</Badge>;
    if (result.ok) return <Badge variant="success" size="sm">{result.status} OK</Badge>;
    if (result.status === 404) return <Badge variant="warning" size="sm">404 No Data</Badge>;
    return <Badge variant="error" size="sm">{result.status} Error</Badge>;
  };

  return (
    <Card variant="elevated" className="border-2 border-blue-500/30">
      <Card.Header>
        <div className="flex items-center justify-between w-full">
          <div>
            <Card.Title className="flex items-center text-blue-400">
              <AlertCircle className="w-5 h-5 mr-2" />
              Endpoint Diagnostics
            </Card.Title>
            <Card.Description>
              Test all player odds endpoints to verify deployment
            </Card.Description>
          </div>
          <Button 
            variant="primary" 
            size="md"
            onClick={testEndpoints}
            disabled={testing}
          >
            {testing ? (
              <>
                <Loader className="w-4 h-4 mr-2 animate-spin" />
                Testing...
              </>
            ) : (
              'Run Tests'
            )}
          </Button>
        </div>
      </Card.Header>

      <Card.Content>
        <div className="space-y-3">
          {endpoints.map((endpoint) => {
            const result = results[endpoint.key];
            
            return (
              <div
                key={endpoint.key}
                className="flex items-center justify-between p-4 bg-dark-800 rounded-lg border border-dark-700"
              >
                <div className="flex items-center gap-3 flex-1">
                  {getStatusIcon(result)}
                  <div className="flex-1 min-w-0">
                    <p className="text-white font-medium truncate">
                      {endpoint.name}
                    </p>
                    <p className="text-xs text-slate-500 truncate">
                      {endpoint.url.replace(API_BASE, '')}
                    </p>
                  </div>
                </div>

                <div className="flex items-center gap-3">
                  {result && (
                    <>
                      {result.responseTime > 0 && (
                        <span className="text-xs text-slate-400">
                          {result.responseTime}ms
                        </span>
                      )}
                      {result.ok && result.dataCount > 0 && (
                        <Badge variant="default" size="sm">
                          {result.dataCount} records
                        </Badge>
                      )}
                    </>
                  )}
                  {getStatusBadge(result)}
                </div>
              </div>
            );
          })}
        </div>

        {/* Error Details */}
        {Object.values(results).some(r => r && !r.ok) && (
          <div className="mt-6 p-4 bg-red-500/10 border border-red-500/20 rounded-lg">
            <h4 className="text-red-400 font-semibold mb-2">Errors Found:</h4>
            <div className="space-y-2">
              {endpoints.map((endpoint) => {
                const result = results[endpoint.key];
                if (!result || result.ok) return null;
                
                return (
                  <div key={endpoint.key} className="text-sm">
                    <span className="text-red-300 font-medium">{endpoint.name}:</span>{' '}
                    <span className="text-red-400">{result.error || 'Unknown error'}</span>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Success Summary */}
        {Object.keys(results).length > 0 && !testing && (
          <div className="mt-6 p-4 bg-blue-500/10 border border-blue-500/20 rounded-lg">
            <div className="flex items-center justify-between">
              <span className="text-blue-300">
                {Object.values(results).filter(r => r.ok).length} / {endpoints.length} endpoints working
              </span>
              <span className="text-xs text-blue-400">
                Avg response time: {Math.round(
                  Object.values(results).reduce((sum, r) => sum + (r?.responseTime || 0), 0) / endpoints.length
                )}ms
              </span>
            </div>
          </div>
        )}
      </Card.Content>

      <Card.Footer>
        <div className="text-sm text-slate-400">
          <span className="font-medium text-slate-300">Note:</span> 404 errors on best-odds are expected 
          when no data exists for the query. Empty results on streaks/sharp-movement are also normal.
        </div>
      </Card.Footer>
    </Card>
  );
};

export default EndpointDiagnostics;
