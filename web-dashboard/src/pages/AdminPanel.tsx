import { useEffect, useState } from 'react';
import { api } from '../api';
import type { CRIWeights } from '../types';

function AdminPanel() {
  const [weights, setWeights] = useState<CRIWeights | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [formValues, setFormValues] = useState({
    netCarbonPosition: 0.5,
    socTrend: 0.3,
    managementPractices: 0.2
  });
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    fetchWeights();
  }, []);

  const fetchWeights = async () => {
    setLoading(true);
    setError(null);

    try {
      const data = await api.getCRIWeights();
      setWeights(data);
      setFormValues(data.weights);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load CRI weights');
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (field: keyof typeof formValues, value: string) => {
    const numValue = parseFloat(value);
    if (!isNaN(numValue)) {
      setFormValues(prev => ({
        ...prev,
        [field]: numValue
      }));
    }
  };

  const calculateSum = () => {
    return formValues.netCarbonPosition + formValues.socTrend + formValues.managementPractices;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    setSuccessMessage(null);

    const sum = calculateSum();
    if (Math.abs(sum - 1.0) > 0.001) {
      setError(`Weights must sum to 1.0 (100%). Current sum: ${sum.toFixed(3)}`);
      setSubmitting(false);
      return;
    }

    try {
      const result = await api.updateCRIWeights(formValues);
      setWeights(result);
      setSuccessMessage('CRI weights updated successfully!');
      setTimeout(() => setSuccessMessage(null), 5000);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update CRI weights');
    } finally {
      setSubmitting(false);
    }
  };

  const sum = calculateSum();
  const isValidSum = Math.abs(sum - 1.0) <= 0.001;

  return (
    <>
      <div className="page-header">
        <h2>⚙️ Admin Panel</h2>
        <span className="page-header-sub">CRI Weights Configuration</span>
      </div>

      <div className="container">
        <div className="card" style={{ maxWidth: '860px', margin: '0 auto' }}>
          <h2>Carbon Readiness Index Weights</h2>

          {loading && (
            <div className="loading">
              <div className="loading-spinner" />
              <div className="loading-text">Loading current weights...</div>
            </div>
          )}

          {error && (
            <div className="error">
              <strong>Error:</strong> {error}
            </div>
          )}

          {successMessage && (
            <div className="success-message">
              <strong>Success:</strong> {successMessage}
            </div>
          )}

          {!loading && weights && (
            <>
              <div className="breakdown" style={{ marginBottom: '28px' }}>
                <h3>📋 Current Configuration</h3>
                <div className="breakdown-item">
                  <span className="breakdown-label">Config ID</span>
                  <span className="breakdown-value" style={{ fontFamily: "'Fira Code', monospace", fontSize: '12px' }}>
                    {weights.configId}
                  </span>
                </div>
                <div className="breakdown-item">
                  <span className="breakdown-label">Version</span>
                  <span className="breakdown-value">v{weights.version}</span>
                </div>
                <div className="breakdown-item">
                  <span className="breakdown-label">Last Updated</span>
                  <span className="breakdown-value" style={{ fontSize: '13px' }}>
                    {weights.updatedAt ? new Date(weights.updatedAt).toLocaleString() : 'Never'}
                  </span>
                </div>
                <div className="breakdown-item">
                  <span className="breakdown-label">Updated By</span>
                  <span className="breakdown-value" style={{ fontSize: '13px' }}>
                    {weights.updatedBy}
                  </span>
                </div>
              </div>

              <form onSubmit={handleSubmit} className="admin-form">
                <div className="form-group">
                  <label htmlFor="netCarbonPosition">
                    🌍 Net Carbon Position Weight
                  </label>
                  <input
                    type="number"
                    id="netCarbonPosition"
                    step="0.01"
                    min="0"
                    max="1"
                    value={formValues.netCarbonPosition}
                    onChange={(e) => handleInputChange('netCarbonPosition', e.target.value)}
                    disabled={submitting}
                  />
                  <div className="form-help">
                    Current: {(formValues.netCarbonPosition * 100).toFixed(0)}%
                  </div>
                </div>

                <div className="form-group">
                  <label htmlFor="socTrend">
                    🌱 Soil Organic Carbon Trend Weight
                  </label>
                  <input
                    type="number"
                    id="socTrend"
                    step="0.01"
                    min="0"
                    max="1"
                    value={formValues.socTrend}
                    onChange={(e) => handleInputChange('socTrend', e.target.value)}
                    disabled={submitting}
                  />
                  <div className="form-help">
                    Current: {(formValues.socTrend * 100).toFixed(0)}%
                  </div>
                </div>

                <div className="form-group">
                  <label htmlFor="managementPractices">
                    🚜 Management Practices Weight
                  </label>
                  <input
                    type="number"
                    id="managementPractices"
                    step="0.01"
                    min="0"
                    max="1"
                    value={formValues.managementPractices}
                    onChange={(e) => handleInputChange('managementPractices', e.target.value)}
                    disabled={submitting}
                  />
                  <div className="form-help">
                    Current: {(formValues.managementPractices * 100).toFixed(0)}%
                  </div>
                </div>

                <div className="form-group">
                  <div className={`weight-total ${isValidSum ? 'valid' : 'invalid'}`}>
                    <strong>Total:</strong> {(sum * 100).toFixed(1)}%
                    {!isValidSum && (
                      <span>⚠️ Must equal 100%</span>
                    )}
                    {isValidSum && (
                      <span>✓ Valid</span>
                    )}
                  </div>
                </div>

                <button
                  type="submit"
                  className="button"
                  disabled={submitting || !isValidSum}
                >
                  {submitting ? 'Updating...' : '💾 Update Weights'}
                </button>
              </form>

              <div className="info-box">
                <h3>ℹ️ About CRI Weights</h3>
                <p>
                  The Carbon Readiness Index (CRI) is calculated using a weighted combination of three components:
                </p>
                <ul>
                  <li><strong>Net Carbon Position:</strong> Measures the farm's carbon balance (sequestration vs emissions)</li>
                  <li><strong>Soil Organic Carbon Trend:</strong> Tracks soil health improvement over time</li>
                  <li><strong>Management Practices:</strong> Evaluates sustainable farming practices</li>
                </ul>
                <p style={{ marginTop: '12px' }}>
                  Weights must sum to 1.0 (100%). Changes will affect all future CRI calculations.
                </p>
              </div>
            </>
          )}
        </div>
      </div>
    </>
  );
}

export default AdminPanel;
