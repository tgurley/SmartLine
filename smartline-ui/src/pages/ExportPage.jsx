import { useState, useEffect } from 'react';
import { Download, FileText, Filter, X, Calendar, TrendingUp } from 'lucide-react';
import Card from '../components/ui/Card';
import Button from '../components/ui/Button';
import Badge from '../components/ui/Badge';

const API_BASE = 'https://smartline-production.up.railway.app';

const ExportPage = () => {
  const [filters, setFilters] = useState({
    start_date: '',
    end_date: '',
    bookmaker: '',
    market: '',
    status: '',
    search: ''
  });

  const [filterOptions, setFilterOptions] = useState({
    bookmakers: [],
    markets: [],
    sports: [],
    statuses: []
  });

  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(false);
  const [exporting, setExporting] = useState(false);

  useEffect(() => {
    fetchFilterOptions();
    fetchSummary();
  }, []);

  useEffect(() => {
    fetchSummary();
  }, [filters]);

  const fetchFilterOptions = async () => {
    try {
      const response = await fetch(`${API_BASE}/bankroll/export/filter-options?user_id=1`);
      const data = await response.json();
      setFilterOptions(data);
    } catch (error) {
      console.error('Error fetching filter options:', error);
    }
  };

  const fetchSummary = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams({
        user_id: '1',
        ...Object.fromEntries(
          Object.entries(filters).filter(([_, v]) => v !== '')
        )
      });

      const response = await fetch(`${API_BASE}/bankroll/export/summary?${params}`);
      const data = await response.json();
      setSummary(data);
    } catch (error) {
      console.error('Error fetching summary:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleFilterChange = (key, value) => {
    setFilters(prev => ({ ...prev, [key]: value }));
  };

  const clearFilters = () => {
    setFilters({
      start_date: '',
      end_date: '',
      bookmaker: '',
      market: '',
      status: '',
      search: ''
    });
  };

  const hasActiveFilters = Object.values(filters).some(v => v !== '');

  const exportCSV = async () => {
    try {
      setExporting(true);
      
      const params = new URLSearchParams({
        user_id: '1',
        ...Object.fromEntries(
          Object.entries(filters).filter(([_, v]) => v !== '')
        )
      });

      const response = await fetch(`${API_BASE}/bankroll/export/csv?${params}`);
      
      if (!response.ok) throw new Error('Export failed');

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `bets_export_${new Date().toISOString().split('T')[0]}.csv`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error) {
      console.error('Error exporting CSV:', error);
      alert('Failed to export CSV. Please try again.');
    } finally {
      setExporting(false);
    }
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0
    }).format(amount);
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    });
  };

  return (
    <div className="space-y-6 pb-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <div className="flex items-center gap-3 mb-2">
            <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-blue-500 to-cyan-500 flex items-center justify-center">
              <Download className="w-6 h-6 text-white" />
            </div>
            <h1 className="text-3xl font-display font-bold text-white">
              Export & Reports
            </h1>
          </div>
          <p className="text-slate-400">
            Download your betting data for analysis
          </p>
        </div>
      </div>

      {/* Filters */}
      <Card variant="elevated">
        <Card.Header>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Filter className="w-5 h-5 text-slate-400" />
              <h2 className="text-lg font-semibold text-white">Filters</h2>
              {hasActiveFilters && (
                <Badge variant="primary" size="sm">
                  {Object.values(filters).filter(v => v !== '').length} active
                </Badge>
              )}
            </div>
            {hasActiveFilters && (
              <Button
                variant="ghost"
                size="sm"
                onClick={clearFilters}
              >
                <X className="w-4 h-4 mr-1" />
                Clear All
              </Button>
            )}
          </div>
        </Card.Header>
        <Card.Content>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {/* Date Range */}
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Start Date
              </label>
              <input
                type="date"
                value={filters.start_date}
                onChange={(e) => handleFilterChange('start_date', e.target.value)}
                className="w-full bg-dark-700 border border-dark-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-blue-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                End Date
              </label>
              <input
                type="date"
                value={filters.end_date}
                onChange={(e) => handleFilterChange('end_date', e.target.value)}
                className="w-full bg-dark-700 border border-dark-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-blue-500"
              />
            </div>

            {/* Bookmaker */}
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Bookmaker
              </label>
              <select
                value={filters.bookmaker}
                onChange={(e) => handleFilterChange('bookmaker', e.target.value)}
                className="w-full bg-dark-700 border border-dark-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-blue-500"
              >
                <option value="">All Bookmakers</option>
                {filterOptions.bookmakers.map(book => (
                  <option key={book} value={book}>{book}</option>
                ))}
              </select>
            </div>

            {/* Market */}
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Market
              </label>
              <select
                value={filters.market}
                onChange={(e) => handleFilterChange('market', e.target.value)}
                className="w-full bg-dark-700 border border-dark-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-blue-500"
              >
                <option value="">All Markets</option>
                {filterOptions.markets.map(market => (
                  <option key={market} value={market}>{market}</option>
                ))}
              </select>
            </div>

            {/* Status */}
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Status
              </label>
              <select
                value={filters.status}
                onChange={(e) => handleFilterChange('status', e.target.value)}
                className="w-full bg-dark-700 border border-dark-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-blue-500"
              >
                <option value="">All Statuses</option>
                <option value="won">Won</option>
                <option value="lost">Lost</option>
                <option value="push">Push</option>
                <option value="pending">Pending</option>
                <option value="cancelled">Cancelled</option>
              </select>
            </div>

            {/* Search */}
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Search
              </label>
              <input
                type="text"
                value={filters.search}
                onChange={(e) => handleFilterChange('search', e.target.value)}
                placeholder="Search notes..."
                className="w-full bg-dark-700 border border-dark-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-blue-500"
              />
            </div>
          </div>
        </Card.Content>
      </Card>

      {/* Summary Preview */}
      {summary && (
        <Card variant="glass">
          <Card.Header>
            <div className="flex items-center gap-2">
              <TrendingUp className="w-5 h-5 text-slate-400" />
              <h2 className="text-lg font-semibold text-white">Export Preview</h2>
            </div>
          </Card.Header>
          <Card.Content>
            {loading ? (
              <div className="text-center py-8">
                <div className="inline-block w-6 h-6 border-2 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
                <p className="text-slate-400 text-sm mt-2">Loading summary...</p>
              </div>
            ) : (
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div>
                  <p className="text-xs text-slate-500 mb-1">Total Bets</p>
                  <p className="text-2xl font-bold text-white">{summary.total_bets}</p>
                </div>
                <div>
                  <p className="text-xs text-slate-500 mb-1">Win Rate</p>
                  <p className="text-2xl font-bold text-white">{summary.win_rate}%</p>
                </div>
                <div>
                  <p className="text-xs text-slate-500 mb-1">Total Staked</p>
                  <p className="text-2xl font-bold font-mono text-white">
                    {formatCurrency(summary.total_staked)}
                  </p>
                </div>
                <div>
                  <p className="text-xs text-slate-500 mb-1">Profit/Loss</p>
                  <p className={`text-2xl font-bold font-mono ${
                    summary.total_profit_loss >= 0 ? 'text-emerald-400' : 'text-red-400'
                  }`}>
                    {formatCurrency(summary.total_profit_loss)}
                  </p>
                </div>
                <div className="col-span-2 md:col-span-4 pt-3 border-t border-dark-700">
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
                    <div>
                      <p className="text-slate-500">Won: <span className="text-emerald-400 font-semibold">{summary.won_bets}</span></p>
                    </div>
                    <div>
                      <p className="text-slate-500">Lost: <span className="text-red-400 font-semibold">{summary.lost_bets}</span></p>
                    </div>
                    <div>
                      <p className="text-slate-500">Push: <span className="text-slate-400 font-semibold">{summary.push_bets}</span></p>
                    </div>
                    <div>
                      <p className="text-slate-500">Pending: <span className="text-blue-400 font-semibold">{summary.pending_bets}</span></p>
                    </div>
                  </div>
                </div>
                {summary.earliest_bet && summary.latest_bet && (
                  <div className="col-span-2 md:col-span-4 pt-3 border-t border-dark-700">
                    <div className="flex items-center gap-2 text-sm text-slate-400">
                      <Calendar className="w-4 h-4" />
                      <span>
                        {formatDate(summary.earliest_bet)} - {formatDate(summary.latest_bet)}
                        {' '}({summary.date_range_days} days)
                      </span>
                    </div>
                  </div>
                )}
              </div>
            )}
          </Card.Content>
        </Card>
      )}

      {/* Export Options */}
      <Card variant="elevated">
        <Card.Header>
          <div className="flex items-center gap-2">
            <FileText className="w-5 h-5 text-slate-400" />
            <h2 className="text-lg font-semibold text-white">Export Options</h2>
          </div>
        </Card.Header>
        <Card.Content>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* CSV Export */}
            <Card variant="glass" hover className="cursor-pointer" onClick={exportCSV}>
              <Card.Content className="py-6 text-center">
                <div className="w-12 h-12 rounded-lg bg-emerald-500/20 flex items-center justify-center mx-auto mb-3">
                  <FileText className="w-6 h-6 text-emerald-400" />
                </div>
                <h3 className="text-lg font-semibold text-white mb-2">CSV Export</h3>
                <p className="text-sm text-slate-400 mb-4">
                  Download as spreadsheet-compatible CSV file
                </p>
                <Button
                  variant="primary"
                  size="sm"
                  disabled={exporting || !summary || summary.total_bets === 0}
                  className="w-full"
                >
                  {exporting ? (
                    <>
                      <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2"></div>
                      Exporting...
                    </>
                  ) : (
                    <>
                      <Download className="w-4 h-4 mr-2" />
                      Download CSV
                    </>
                  )}
                </Button>
              </Card.Content>
            </Card>

            {/* Excel Export - Coming Soon */}
            <Card variant="glass" className="opacity-50">
              <Card.Content className="py-6 text-center">
                <div className="w-12 h-12 rounded-lg bg-blue-500/20 flex items-center justify-center mx-auto mb-3">
                  <FileText className="w-6 h-6 text-blue-400" />
                </div>
                <h3 className="text-lg font-semibold text-white mb-2">Excel Export</h3>
                <p className="text-sm text-slate-400 mb-4">
                  Advanced export with formulas and charts
                </p>
                <Button variant="ghost" size="sm" className="w-full" disabled>
                  Coming Soon
                </Button>
              </Card.Content>
            </Card>

            {/* PDF Report - Coming Soon */}
            <Card variant="glass" className="opacity-50">
              <Card.Content className="py-6 text-center">
                <div className="w-12 h-12 rounded-lg bg-purple-500/20 flex items-center justify-center mx-auto mb-3">
                  <FileText className="w-6 h-6 text-purple-400" />
                </div>
                <h3 className="text-lg font-semibold text-white mb-2">PDF Report</h3>
                <p className="text-sm text-slate-400 mb-4">
                  Professional formatted report
                </p>
                <Button variant="ghost" size="sm" className="w-full" disabled>
                  Coming Soon
                </Button>
              </Card.Content>
            </Card>
          </div>

          {summary && summary.total_bets === 0 && (
            <div className="mt-4 p-4 bg-amber-500/10 border border-amber-500/30 rounded-lg">
              <p className="text-sm text-amber-300">
                No bets found matching your filters. Try adjusting the filters above.
              </p>
            </div>
          )}
        </Card.Content>
      </Card>
    </div>
  );
};

export default ExportPage;
