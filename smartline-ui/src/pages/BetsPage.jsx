import { useState, useEffect } from 'react';
import { List, ArrowLeft, Download } from 'lucide-react';
import { Link } from 'react-router-dom';
import Button from '../components/ui/Button';
import FullBetsTable from '../components/bankroll/FullBetsTable';
import EditBetModal from '../components/bankroll/EditBetModal';
import ExportModal from '../components/bankroll/ExportModal';

const API_BASE = 'https://smartline-production.up.railway.app';

const BetsPage = () => {
  const [accounts, setAccounts] = useState([]);
  const [editingBet, setEditingBet] = useState(null);
  const [showExportModal, setShowExportModal] = useState(false);
  const [refreshTrigger, setRefreshTrigger] = useState(0);

  useEffect(() => {
    fetchAccounts();
  }, []);

  const fetchAccounts = async () => {
    try {
      const response = await fetch(`${API_BASE}/bankroll/accounts?user_id=1`);
      const data = await response.json();
      setAccounts(data);
    } catch (error) {
      console.error('Error fetching accounts:', error);
    }
  };

  const handleBetUpdated = () => {
    setRefreshTrigger(prev => prev + 1);
  };

  const handleEditBet = (bet) => {
    setEditingBet(bet);
  };

  const closeEditModal = () => {
    setEditingBet(null);
  };

  return (
    <div className="space-y-6 pb-8">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <div className="flex items-center gap-3 mb-2">
            <Link to="/bankroll">
              <button className="p-2 hover:bg-dark-800 rounded-lg transition-colors">
                <ArrowLeft className="w-5 h-5 text-slate-400" />
              </button>
            </Link>
            <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-blue-500 to-cyan-500 flex items-center justify-center">
              <List className="w-6 h-6 text-white" />
            </div>
            <h1 className="text-3xl font-display font-bold text-white">
              All Bets
            </h1>
          </div>
          <p className="text-slate-400 ml-14">
            Complete bet history with advanced filtering
          </p>
        </div>
        
        <Button 
          variant="primary"
          size="md"
          onClick={() => setShowExportModal(true)}
        >
          <Download className="w-4 h-4 mr-2" />
          Export
        </Button>
      </div>

      {/* Full Bets Table */}
      <FullBetsTable 
        key={refreshTrigger}
        onBetUpdated={handleBetUpdated}
        onEditBet={handleEditBet}
      />

      {/* Edit Modal */}
      {editingBet && (
        <EditBetModal
          bet={editingBet}
          accounts={accounts}
          onClose={closeEditModal}
          onBetUpdated={() => {
            handleBetUpdated();
            closeEditModal();
          }}
        />
      )}

      {/* Export Modal */}
      {showExportModal && (
        <ExportModal
          onClose={() => setShowExportModal(false)}
        />
      )}
    </div>
  );
};

export default BetsPage;