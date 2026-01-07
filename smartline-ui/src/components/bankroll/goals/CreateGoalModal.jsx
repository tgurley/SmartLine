import { useState } from 'react';
import { X, Target } from 'lucide-react';
import Button from '../../ui/Button';

const CreateGoalModal = ({ onClose, onCreate }) => {
  const [formData, setFormData] = useState({
    goal_type: 'weekly',
    goal_amount: '',
    description: '',
    start_date: new Date().toISOString().split('T')[0],
    end_date: ''
  });

  const [errors, setErrors] = useState({});

  const calculateEndDate = (type, startDate) => {
    const start = new Date(startDate);
    let end = new Date(start);

    switch (type) {
      case 'daily':
        end.setDate(start.getDate() + 1);
        break;
      case 'weekly':
        end.setDate(start.getDate() + 7);
        break;
      case 'monthly':
        end.setMonth(start.getMonth() + 1);
        break;
      case 'yearly':
        end.setFullYear(start.getFullYear() + 1);
        break;
    }

    return end.toISOString().split('T')[0];
  };

  const handleTypeChange = (type) => {
    const endDate = calculateEndDate(type, formData.start_date);
    setFormData({ ...formData, goal_type: type, end_date: endDate });
  };

  const handleStartDateChange = (date) => {
    const endDate = calculateEndDate(formData.goal_type, date);
    setFormData({ ...formData, start_date: date, end_date: endDate });
  };

  const validate = () => {
    const newErrors = {};

    if (!formData.goal_amount || parseFloat(formData.goal_amount) <= 0) {
      newErrors.goal_amount = 'Goal amount must be greater than 0';
    }

    if (!formData.start_date) {
      newErrors.start_date = 'Start date is required';
    }

    if (!formData.end_date) {
      newErrors.end_date = 'End date is required';
    }

    if (formData.start_date && formData.end_date && new Date(formData.end_date) <= new Date(formData.start_date)) {
      newErrors.end_date = 'End date must be after start date';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    
    if (!validate()) return;

    onCreate(formData);
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-dark-800 rounded-xl max-w-lg w-full border border-dark-700 shadow-2xl">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-dark-700">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center">
              <Target className="w-5 h-5 text-white" />
            </div>
            <h2 className="text-xl font-semibold text-white">Create New Goal</h2>
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
          {/* Goal Type */}
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">
              Goal Type
            </label>
            <div className="grid grid-cols-4 gap-2">
              {['daily', 'weekly', 'monthly', 'yearly'].map((type) => (
                <button
                  key={type}
                  type="button"
                  onClick={() => handleTypeChange(type)}
                  className={`px-3 py-2 rounded-lg text-sm font-medium transition-all ${
                    formData.goal_type === type
                      ? 'bg-purple-500 text-white'
                      : 'bg-dark-700 text-slate-400 hover:bg-dark-600 hover:text-white'
                  }`}
                >
                  {type.charAt(0).toUpperCase() + type.slice(1)}
                </button>
              ))}
            </div>
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
                } rounded-lg px-9 py-2 text-white focus:outline-none focus:border-purple-500`}
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
              className="w-full bg-dark-700 border border-dark-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-purple-500"
              placeholder="e.g., Holiday betting fund, Monthly profit target"
            />
          </div>

          {/* Date Range */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Start Date
              </label>
              <input
                type="date"
                value={formData.start_date}
                onChange={(e) => handleStartDateChange(e.target.value)}
                className={`w-full bg-dark-700 border ${
                  errors.start_date ? 'border-red-500' : 'border-dark-600'
                } rounded-lg px-3 py-2 text-white focus:outline-none focus:border-purple-500`}
              />
              {errors.start_date && (
                <p className="text-red-400 text-xs mt-1">{errors.start_date}</p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                End Date
              </label>
              <input
                type="date"
                value={formData.end_date}
                onChange={(e) => setFormData({ ...formData, end_date: e.target.value })}
                className={`w-full bg-dark-700 border ${
                  errors.end_date ? 'border-red-500' : 'border-dark-600'
                } rounded-lg px-3 py-2 text-white focus:outline-none focus:border-purple-500`}
              />
              {errors.end_date && (
                <p className="text-red-400 text-xs mt-1">{errors.end_date}</p>
              )}
            </div>
          </div>

          {/* Preview */}
          {formData.goal_amount && parseFloat(formData.goal_amount) > 0 && (
            <div className="bg-purple-500/10 border border-purple-500/30 rounded-lg p-4">
              <p className="text-sm text-purple-300">
                Goal: Earn <span className="font-bold">${parseFloat(formData.goal_amount).toFixed(2)}</span>
                {' '}in{' '}
                {formData.goal_type === 'daily' ? '1 day' :
                 formData.goal_type === 'weekly' ? '7 days' :
                 formData.goal_type === 'monthly' ? '1 month' :
                 '1 year'}
              </p>
            </div>
          )}

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
              Create Goal
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default CreateGoalModal;
