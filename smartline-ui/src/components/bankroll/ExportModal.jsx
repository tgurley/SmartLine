import { useState, useEffect } from 'react';
import { X, Download, Filter, FileText, TrendingUp } from 'lucide-react';
import Button from '../ui/Button';
import Badge from '../ui/Badge';

const API_BASE = 'https://smartline-production.up.railway.app';

const ExportModal = ({ onClose, currentFilters = {} }) => {
  const [filters, setFilters] = useState({
    start_date: currentFilters.start_date || '',
    end_date: currentFilters.end_date || '',
    bookmaker: currentFilters.bookmaker || '',
    market: currentFilters.market || '',
    status: currentFilters.status || '',
    search: currentFilters.search || ''
  });

  const [filterOptions, setFilterOptions] = useState({
    bookmakers: [],
    markets: [],
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
      
      setTimeout(() => {
        onClose();
      }, 500);
    } catch (error) {
      console.error('Error exporting CSV:', error);
      alert('Failed to export CSV. Please try again.');
    } finally {
      setExporting(false);
    }
  };

  const exportExcel = async () => {
    try {
      setExporting(true);
      
      const params = new URLSearchParams({
        user_id: '1',
        ...Object.fromEntries(
          Object.entries(filters).filter(([_, v]) => v !== '')
        )
      });

      const response = await fetch(`${API_BASE}/bankroll/export/excel?${params}`);
      
      if (!response.ok) throw new Error('Export failed');

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `bets_export_${new Date().toISOString().split('T')[0]}.xlsx`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      
      setTimeout(() => {
        onClose();
      }, 500);
    } catch (error) {
      console.error('Error exporting Excel:', error);
      alert('Failed to export Excel. Please try again.');
    } finally {
      setExporting(false);
    }
  };

  const exportPDF = async () => {
    try {
      setExporting(true);
      
      const params = new URLSearchParams({
        user_id: '1',
        ...Object.fromEntries(
          Object.entries(filters).filter(([_, v]) => v !== '')
        )
      });

      const response = await fetch(`${API_BASE}/bankroll/export/pdf-report?${params}`);
      
      if (!response.ok) throw new Error('Export failed');

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `betting_report_${new Date().toISOString().split('T')[0]}.pdf`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      
      setTimeout(() => {
        onClose();
      }, 500);
    } catch (error) {
      console.error('Error exporting PDF:', error);
      alert('Failed to export PDF. Please try again.');
    } finally {
      setExporting(false);
    }
  };

  const exportTaxReport = async () => {
    try {
      setExporting(true);
      
      const year = new Date().getFullYear();
      const response = await fetch(`${API_BASE}/bankroll/export/tax-report/pdf?user_id=1&year=${year}`);
      
      if (!response.ok) throw new Error('Export failed');

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `tax_report_${year}.txt`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      
      setTimeout(() => {
        onClose();
      }, 500);
    } catch (error) {
      console.error('Error exporting tax report:', error);
      alert('Failed to export tax report. Please try again.');
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

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-dark-800 rounded-xl max-w-4xl w-full border border-dark-700 shadow-2xl max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="sticky top-0 bg-dark-800 border-b border-dark-700 p-6 z-10">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-blue-500 to-cyan-500 flex items-center justify-center">
                <Download className="w-5 h-5 text-white" />
              </div>
              <div>
                <h2 className="text-xl font-semibold text-white">Export Bets</h2>
                <p className="text-sm text-slate-400">Download your betting data</p>
              </div>
            </div>
            <button
              onClick={onClose}
              className="text-slate-400 hover:text-white transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        <div className="p-6 space-y-6">
          {/* Filters */}
          <div className="bg-dark-900 rounded-lg p-4 border border-dark-700">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <Filter className="w-5 h-5 text-slate-400" />
                <h3 className="font-semibold text-white">Filters</h3>
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

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {/* Start Date */}
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  Start Date
                </label>
                <input
                  type="date"
                  value={filters.start_date}
                  onChange={(e) => handleFilterChange('start_date', e.target.value)}
                  className="w-full bg-dark-700 border border-dark-600 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-blue-500"
                />
              </div>

              {/* End Date */}
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  End Date
                </label>
                <input
                  type="date"
                  value={filters.end_date}
                  onChange={(e) => handleFilterChange('end_date', e.target.value)}
                  className="w-full bg-dark-700 border border-dark-600 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-blue-500"
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
                  className="w-full bg-dark-700 border border-dark-600 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-blue-500"
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
                  className="w-full bg-dark-700 border border-dark-600 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-blue-500"
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
                  className="w-full bg-dark-700 border border-dark-600 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-blue-500"
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
                  Search Notes
                </label>
                <input
                  type="text"
                  value={filters.search}
                  onChange={(e) => handleFilterChange('search', e.target.value)}
                  placeholder="Search..."
                  className="w-full bg-dark-700 border border-dark-600 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-blue-500"
                />
              </div>
            </div>
          </div>

          {/* Summary Preview */}
          {summary && (
            <div className="bg-dark-900 rounded-lg p-4 border border-dark-700">
              <div className="flex items-center gap-2 mb-4">
                <TrendingUp className="w-5 h-5 text-slate-400" />
                <h3 className="font-semibold text-white">Export Preview</h3>
              </div>

              {loading ? (
                <div className="text-center py-4">
                  <div className="inline-block w-5 h-5 border-2 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
                  <p className="text-slate-400 text-sm mt-2">Loading summary...</p>
                </div>
              ) : (
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div>
                    <p className="text-xs text-slate-500 mb-1">Total Bets</p>
                    <p className="text-xl font-bold text-white">{summary.total_bets}</p>
                  </div>
                  <div>
                    <p className="text-xs text-slate-500 mb-1">Win Rate</p>
                    <p className="text-xl font-bold text-white">{summary.win_rate}%</p>
                  </div>
                  <div>
                    <p className="text-xs text-slate-500 mb-1">Total Staked</p>
                    <p className="text-xl font-bold font-mono text-white">
                      {formatCurrency(summary.total_staked)}
                    </p>
                  </div>
                  <div>
                    <p className="text-xs text-slate-500 mb-1">Profit/Loss</p>
                    <p className={`text-xl font-bold font-mono ${
                      summary.total_profit_loss >= 0 ? 'text-emerald-400' : 'text-red-400'
                    }`}>
                      {formatCurrency(summary.total_profit_loss)}
                    </p>
                  </div>
                </div>
              )}

              {summary && summary.total_bets === 0 && (
                <div className="mt-4 p-3 bg-amber-500/10 border border-amber-500/30 rounded-lg">
                  <p className="text-sm text-amber-300">
                    No bets found matching your filters. Try adjusting the filters above.
                  </p>
                </div>
              )}
            </div>
          )}

          {/* Export Button */}
          <div className="grid grid-cols-2 gap-3">
            <Button
              variant="primary"
              onClick={exportCSV}
              disabled={exporting || !summary || summary.total_bets === 0}
              className="flex-1"
            >
              {exporting ? (
                <>
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2"></div>
                  Exporting...
                </>
              ) : (
                <>
                  <Download className="w-4 h-4 mr-2" />
                  CSV ({summary?.total_bets || 0})
                </>
              )}
            </Button>

            <Button
              variant="primary"
              onClick={exportExcel}
              disabled={exporting || !summary || summary.total_bets === 0}
              className="flex-1"
            >
              {exporting ? (
                <>
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2"></div>
                  Exporting...
                </>
              ) : (
                <>
                  <Download className="w-4 h-4 mr-2" />
                  Excel ({summary?.total_bets || 0})
                </>
              )}
            </Button>

            <Button
              variant="secondary"
              onClick={exportPDF}
              disabled={exporting || !summary || summary.total_bets === 0}
              className="flex-1"
            >
              {exporting ? (
                <>
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2"></div>
                  Exporting...
                </>
              ) : (
                <>
                  <Download className="w-4 h-4 mr-2" />
                  PDF Report
                </>
              )}
            </Button>

            <Button
              variant="secondary"
              onClick={exportTaxReport}
              disabled={exporting}
              className="flex-1"
            >
              {exporting ? (
                <>
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2"></div>
                  Exporting...
                </>
              ) : (
                <>
                  <Download className="w-4 h-4 mr-2" />
                  Tax Report {new Date().getFullYear()}
                </>
              )}
            </Button>
          </div>

          <Button
            variant="ghost"
            onClick={onClose}
            className="w-full mt-2"
          >
            Cancel
          </Button>
        </div>
      </div>
    </div>
  );
};

export default ExportModal;
