import { useState, useEffect } from 'react';
import { Plus, Target, TrendingUp, Calendar, CheckCircle, Trash2, Edit2, Award } from 'lucide-react';
import Card from '../components/ui/Card';
import Button from '../components/ui/Button';
import Badge from '../components/ui/Badge';
import CreateGoalModal from '../components/bankroll/goals/CreateGoalModal';
import EditGoalModal from '../components/bankroll/goals/EditGoalModal';

const API_BASE = 'https://smartline-production.up.railway.app';

const GoalsDashboard = () => {
  const [goals, setGoals] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [editingGoal, setEditingGoal] = useState(null);
  const [filter, setFilter] = useState('active');

  useEffect(() => {
    fetchGoals();
  }, []);

  const fetchGoals = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${API_BASE}/bankroll/goals?user_id=1&status=all`);
      const data = await response.json();
      setGoals(data);
    } catch (error) {
      console.error('Error fetching goals:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateGoal = async (goalData) => {
    try {
      const response = await fetch(`${API_BASE}/bankroll/goals?user_id=1`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(goalData)
      });
      
      if (response.ok) {
        await fetchGoals();
        setShowCreateModal(false);
      } else {
        const error = await response.json();
        console.error('Error creating goal:', error);
        alert('Failed to create goal: ' + (error.detail || 'Unknown error'));
      }
    } catch (error) {
      console.error('Error creating goal:', error);
      alert('Failed to create goal. Please try again.');
    }
  };

  const handleUpdateGoal = async (goalId, updates) => {
    try {
      const response = await fetch(`${API_BASE}/bankroll/goals/${goalId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(updates)
      });
      
      if (response.ok) {
        await fetchGoals();
        setEditingGoal(null);
      } else {
        const error = await response.json();
        console.error('Error updating goal:', error);
        alert('Failed to update goal: ' + (error.detail || 'Unknown error'));
      }
    } catch (error) {
      console.error('Error updating goal:', error);
      alert('Failed to update goal. Please try again.');
    }
  };

  const handleDeleteGoal = async (goalId) => {
    if (!confirm('Are you sure you want to delete this goal?')) return;
    
    try {
      const response = await fetch(`${API_BASE}/bankroll/goals/${goalId}`, {
        method: 'DELETE'
      });
      
      if (response.ok) {
        await fetchGoals();
      } else {
        const error = await response.json();
        console.error('Error deleting goal:', error);
        alert('Failed to delete goal: ' + (error.detail || 'Unknown error'));
      }
    } catch (error) {
      console.error('Error deleting goal:', error);
      alert('Failed to delete goal. Please try again.');
    }
  };

  const handleCompleteGoal = async (goalId) => {
    await handleUpdateGoal(goalId, { status: 'completed' });
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0
    }).format(parseFloat(amount));
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    });
  };

  const getGoalTypeColor = (type) => {
    const colors = {
      daily: 'blue',
      weekly: 'purple',
      monthly: 'emerald',
      yearly: 'amber'
    };
    return colors[type] || 'slate';
  };

  const activeGoals = goals.filter(g => g.status === 'active');
  const completedGoals = goals.filter(g => g.status === 'completed');
  const failedGoals = goals.filter(g => g.status === 'failed');

  const displayedGoals = filter === 'active' ? activeGoals :
                         filter === 'completed' ? completedGoals :
                         goals;

  return (
    <div className="space-y-6 pb-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <div className="flex items-center gap-3 mb-2">
            <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center">
              <Target className="w-6 h-6 text-white" />
            </div>
            <h1 className="text-3xl font-display font-bold text-white">
              Goals
            </h1>
          </div>
          <p className="text-slate-400">
            Set targets and track your progress
          </p>
        </div>
        <Button 
          variant="primary" 
          size="md"
          onClick={() => setShowCreateModal(true)}
        >
          <Plus className="w-4 h-4 mr-2" />
          Create Goal
        </Button>
      </div>

      {/* Filter Tabs */}
      <div className="flex gap-2 border-b border-dark-700">
        <button
          onClick={() => setFilter('active')}
          className={`px-4 py-2 font-medium transition-colors border-b-2 ${
            filter === 'active'
              ? 'border-blue-500 text-white'
              : 'border-transparent text-slate-400 hover:text-white'
          }`}
        >
          Active ({activeGoals.length})
        </button>
        <button
          onClick={() => setFilter('completed')}
          className={`px-4 py-2 font-medium transition-colors border-b-2 ${
            filter === 'completed'
              ? 'border-emerald-500 text-white'
              : 'border-transparent text-slate-400 hover:text-white'
          }`}
        >
          Completed ({completedGoals.length})
        </button>
        <button
          onClick={() => setFilter('all')}
          className={`px-4 py-2 font-medium transition-colors border-b-2 ${
            filter === 'all'
              ? 'border-purple-500 text-white'
              : 'border-transparent text-slate-400 hover:text-white'
          }`}
        >
          All Goals ({goals.length})
        </button>
      </div>

      {/* Summary Stats */}
      {filter === 'active' && activeGoals.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Card variant="glass">
            <Card.Content className="py-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-lg bg-blue-500/20 flex items-center justify-center">
                  <Target className="w-5 h-5 text-blue-400" />
                </div>
                <div>
                  <p className="text-sm text-slate-400">Active Goals</p>
                  <p className="text-2xl font-bold text-white">{activeGoals.length}</p>
                </div>
              </div>
            </Card.Content>
          </Card>

          <Card variant="glass">
            <Card.Content className="py-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-lg bg-emerald-500/20 flex items-center justify-center">
                  <CheckCircle className="w-5 h-5 text-emerald-400" />
                </div>
                <div>
                  <p className="text-sm text-slate-400">Completed</p>
                  <p className="text-2xl font-bold text-white">{completedGoals.length}</p>
                </div>
              </div>
            </Card.Content>
          </Card>

          <Card variant="glass">
            <Card.Content className="py-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-lg bg-purple-500/20 flex items-center justify-center">
                  <TrendingUp className="w-5 h-5 text-purple-400" />
                </div>
                <div>
                  <p className="text-sm text-slate-400">Avg Progress</p>
                  <p className="text-2xl font-bold text-white">
                    {activeGoals.length > 0
                      ? (activeGoals.reduce((sum, g) => sum + parseFloat(g.progress_percentage || 0), 0) / activeGoals.length).toFixed(0)
                      : 0}%
                  </p>
                </div>
              </div>
            </Card.Content>
          </Card>
        </div>
      )}

      {/* Goals Grid */}
      {loading ? (
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-64 bg-dark-800 rounded-lg animate-pulse"></div>
          ))}
        </div>
      ) : displayedGoals.length === 0 ? (
        <Card variant="elevated">
          <Card.Content className="py-16 text-center">
            <Target className="w-16 h-16 text-slate-600 mx-auto mb-4" />
            <h3 className="text-xl font-semibold text-white mb-2">No Goals Yet</h3>
            <p className="text-slate-400 mb-6">
              {filter === 'active' 
                ? "Set your first goal to start tracking your progress"
                : filter === 'completed'
                ? "No completed goals yet - keep working towards your targets!"
                : "Create your first goal to get started"}
            </p>
            {filter === 'active' && (
              <Button variant="primary" onClick={() => setShowCreateModal(true)}>
                <Plus className="w-4 h-4 mr-2" />
                Create Your First Goal
              </Button>
            )}
          </Card.Content>
        </Card>
      ) : (
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {displayedGoals.map((goal) => (
            <GoalCard
              key={goal.goal_id}
              goal={goal}
              onEdit={() => setEditingGoal(goal)}
              onDelete={() => handleDeleteGoal(goal.goal_id)}
              onComplete={() => handleCompleteGoal(goal.goal_id)}
              formatCurrency={formatCurrency}
              formatDate={formatDate}
              getGoalTypeColor={getGoalTypeColor}
            />
          ))}
        </div>
      )}

      {/* Modals */}
      {showCreateModal && (
        <CreateGoalModal
          onClose={() => setShowCreateModal(false)}
          onCreate={handleCreateGoal}
        />
      )}

      {editingGoal && (
        <EditGoalModal
          goal={editingGoal}
          onClose={() => setEditingGoal(null)}
          onUpdate={(updates) => handleUpdateGoal(editingGoal.goal_id, updates)}
        />
      )}
    </div>
  );
};

const GoalCard = ({ goal, onEdit, onDelete, onComplete, formatCurrency, formatDate, getGoalTypeColor }) => {
  const progressPercentage = parseFloat(goal.progress_percentage) || 0;
  const isComplete = goal.status === 'completed';
  const isFailed = goal.status === 'failed';
  const isActive = goal.status === 'active';
  const currentProgress = parseFloat(goal.current_progress || 0);
  const goalAmount = parseFloat(goal.goal_amount);
  const daysRemaining = goal.days_remaining;

  const getStatusColor = () => {
    if (isComplete) return 'emerald';
    if (isFailed) return 'red';
    if (progressPercentage >= 75) return 'emerald';
    if (progressPercentage >= 50) return 'blue';
    if (progressPercentage >= 25) return 'amber';
    return 'slate';
  };

  return (
    <Card variant="glass" hover className="relative overflow-hidden">
      {/* Achievement Badge */}
      {isComplete && (
        <div className="absolute top-4 right-4">
          <Award className="w-8 h-8 text-yellow-400 animate-pulse" />
        </div>
      )}

      <Card.Content className="py-6">
        {/* Header */}
        <div className="flex items-start justify-between mb-4">
          <div className="flex-1">
            <Badge variant={getGoalTypeColor(goal.goal_type)} size="sm" className="mb-2">
              {goal.goal_type.charAt(0).toUpperCase() + goal.goal_type.slice(1)}
            </Badge>
            {goal.description && (
              <p className="text-sm text-slate-400 mt-1">{goal.description}</p>
            )}
          </div>
        </div>

        {/* Progress */}
        <div className="space-y-3 mb-4">
          <div className="flex justify-between text-sm">
            <span className="text-slate-400">Progress</span>
            <span className={`font-bold text-${getStatusColor()}-400`}>
              {progressPercentage.toFixed(0)}%
            </span>
          </div>
          <div className="w-full bg-dark-700 rounded-full h-2">
            <div
              className={`h-2 rounded-full transition-all bg-gradient-to-r ${
                isComplete ? 'from-emerald-500 to-teal-500' :
                isFailed ? 'from-red-500 to-red-600' :
                'from-blue-500 to-cyan-500'
              }`}
              style={{ width: `${Math.min(progressPercentage, 100)}%` }}
            ></div>
          </div>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-2 gap-4 mb-4 pb-4 border-b border-dark-700">
          <div>
            <p className="text-xs text-slate-500 mb-1">Current</p>
            <p className={`text-lg font-bold font-mono ${
              currentProgress >= 0 ? 'text-emerald-400' : 'text-red-400'
            }`}>
              {formatCurrency(currentProgress)}
            </p>
          </div>
          <div>
            <p className="text-xs text-slate-500 mb-1">Target</p>
            <p className="text-lg font-bold font-mono text-white">
              {formatCurrency(goalAmount)}
            </p>
          </div>
        </div>

        {/* Date Info */}
        <div className="flex items-center gap-2 text-xs text-slate-400 mb-4">
          <Calendar className="w-3 h-3" />
          <span>
            {formatDate(goal.start_date)} - {formatDate(goal.end_date)}
          </span>
        </div>

        {/* Days Remaining */}
        {isActive && daysRemaining !== null && (
          <div className={`text-sm font-medium mb-4 ${
            daysRemaining <= 2 ? 'text-red-400' :
            daysRemaining <= 7 ? 'text-amber-400' :
            'text-slate-400'
          }`}>
            {daysRemaining > 0 ? `${daysRemaining} days remaining` : 'Due today!'}
          </div>
        )}

        {/* Status Badge */}
        {isComplete && (
          <Badge variant="success" size="sm" className="mb-4">
            <CheckCircle className="w-3 h-3 mr-1" />
            Completed {goal.completed_at && `on ${formatDate(goal.completed_at)}`}
          </Badge>
        )}

        {isFailed && (
          <Badge variant="error" size="sm" className="mb-4">
            Failed
          </Badge>
        )}

        {/* Actions */}
        {isActive && (
          <div className="flex gap-2">
            {progressPercentage >= 100 && (
              <Button
                variant="primary"
                size="sm"
                onClick={onComplete}
                className="flex-1"
              >
                <CheckCircle className="w-3 h-3 mr-1" />
                Mark Complete
              </Button>
            )}
            <Button
              variant="ghost"
              size="sm"
              onClick={onEdit}
            >
              <Edit2 className="w-3 h-3 mr-1" />
              Edit
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={onDelete}
              className="text-red-400 hover:text-red-300"
            >
              <Trash2 className="w-3 h-3" />
            </Button>
          </div>
        )}

        {!isActive && (
          <Button
            variant="ghost"
            size="sm"
            onClick={onDelete}
            className="w-full text-red-400 hover:text-red-300"
          >
            <Trash2 className="w-3 h-3 mr-1" />
            Delete
          </Button>
        )}
      </Card.Content>
    </Card>
  );
};

export default GoalsDashboard;