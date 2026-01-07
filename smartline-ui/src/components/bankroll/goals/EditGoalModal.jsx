import { useState } from 'react';
import { X, Edit2 } from 'lucide-react';
import Button from '../../ui/Button';

const EditGoalModal = ({ goal, onClose, onUpdate }) => {
  const [formData, setFormData] = useState({
    goal_amount: goal.goal_amount,
    description: goal.description || '',
    end_date: goal.end_date.split('T')[0]
  });

  const [errors, setErrors] = useState({});

  const validate = () => {
    const newErrors = {};

    if (!formData.goal_amount || parseFloat(formData.goal_amount) <= 0) {
      newErrors.goal_amount = 'Goal amount must be greater than 0';
    }

    if (!formData.end_date) {
      newErrors.end_date = 'End date is required';
    }

    if (formData.end_date && new Date(formData.end_date) <= new Date(goal.start_date)) {
      newErrors.end_date = 'End date must be after start date';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    
    if (!validate()) return;

    onUpdate(formData);
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-dark-800 rounded-xl max-w-lg w-full border border-dark-700 shadow-2xl">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-dark-700">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-blue-500 to-cyan-500 flex items-center justify-center">
              <Edit2 className="w-5 h-5 text-white" />
            </div>
            <h2 className="text-xl font-semibold text-white">Edit Goal</h2>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-white transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {/* Goal Type (Read-only) */}
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">
              Goal Type
            </label>
            <div className="bg-dark-900 border border-dark-700 rounded-lg px-3 py-2 text-slate-400">
              {goal.goal_type.charAt(0).toUpperCase() + goal.goal_type.slice(1)}
            </div>
            <p className="text-xs text-slate-500 mt-1">Goal type cannot be changed</p>
          </div>

          {/* Goal Amount */}
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">
              Target Profit Amount
            </label>
            <div className="relative">
              <span className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400">$</span>
              <input
                type="number"
                step="0.01"
                value={formData.goal_amount}
                onChange={(e) => setFormData({ ...formData, goal_amount: e.target.value })}
                className={`w-full bg-dark-700 border ${
                  errors.goal_amount ? 'border-red-500' : 'border-dark-600'
                } rounded-lg px-9 py-2 text-white focus:outline-none focus:border-blue-500`}
                placeholder="500.00"
              />
            </div>
            {errors.goal_amount && (
              <p className="text-red-400 text-xs mt-1">{errors.goal_amount}</p>
            )}
          </div>

          {/* Description */}
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">
              Description (Optional)
            </label>
            <input
              type="text"
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              className="w-full bg-dark-700 border border-dark-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-blue-500"
              placeholder="e.g., Holiday betting fund, Monthly profit target"
            />
          </div>

          {/* Date Range */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Start Date
              </label>
              <div className="bg-dark-900 border border-dark-700 rounded-lg px-3 py-2 text-slate-400">
                {new Date(goal.start_date).toLocaleDateString()}
              </div>
              <p className="text-xs text-slate-500 mt-1">Cannot be changed</p>
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                End Date
              </label>
              <input
                type="date"
                value={formData.end_date}
                onChange={(e) => setFormData({ ...formData, end_date: e.target.value })}
                min={goal.start_date.split('T')[0]}
                className={`w-full bg-dark-700 border ${
                  errors.end_date ? 'border-red-500' : 'border-dark-600'
                } rounded-lg px-3 py-2 text-white focus:outline-none focus:border-blue-500`}
              />
              {errors.end_date && (
                <p className="text-red-400 text-xs mt-1">{errors.end_date}</p>
              )}
            </div>
          </div>

          {/* Current Progress */}
          <div className="bg-blue-500/10 border border-blue-500/30 rounded-lg p-4">
            <div className="flex justify-between items-center mb-2">
              <span className="text-sm text-blue-300">Current Progress</span>
              <span className="text-sm font-bold text-blue-300">
                {goal.progress_percentage}%
              </span>
            </div>
            <div className="w-full bg-dark-700 rounded-full h-2">
              <div
                className="h-2 rounded-full bg-gradient-to-r from-blue-500 to-cyan-500"
                style={{ width: `${Math.min(parseFloat(goal.progress_percentage), 100)}%` }}
              ></div>
            </div>
            <p className="text-xs text-slate-400 mt-2">
              ${parseFloat(goal.current_progress || 0).toFixed(2)} / ${parseFloat(formData.goal_amount).toFixed(2)}
            </p>
          </div>

          {/* Actions */}
          <div className="flex gap-3 pt-4">
            <Button
              type="button"
              variant="ghost"
              onClick={onClose}
              className="flex-1"
            >
              Cancel
            </Button>
            <Button
              type="submit"
              variant="primary"
              className="flex-1"
            >
              Update Goal
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default EditGoalModal;
