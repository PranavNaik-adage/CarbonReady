import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
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

    // Validate sum
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
      
      // Clear success message after 5 seconds
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
    <div className="app">
      <header className="header">
        <div className="container">
          <h1>CarbonReady Dashboard</h1>
          <p>Admin Panel</p>
          <nav className="nav">
            <Link to="/dashboard/farm-001">Dashboard</Link>
            <Link to="/admin" className="active">Admin Panel</Link>
          </nav>
        </div>
      </header>

      <div className="container">
        <div className="card" style={{ maxWidth: '800px', margin: '20px auto' }}>
          <h2>Carbon Readiness Index Weights Configuration</h2>

          {loading && <div className="loading">Loading current weights...</div>}

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
              <div className="breakdown" style={{ marginBottom: '30px' }}>
                <h3>Current Configuration</h3>
                <div className="breakdown-item">
                  <span className="breakdown-label">Config ID</span>
                  <span className="breakdown-value">{weights.configId}</span>
                </div>
                <div className="breakdown-item">
                  <span className="breakdown-label">Version</span>
                  <span className="breakdown-value">v{weights.version}</span>
                </div>
                <div className="breakdown-item">
                  <span className="breakdown-label">Last Updated</span>
                  <span className="breakdown-value">
                    {weights.updatedAt ? new Date(weights.updatedAt).toLocaleString() : 'Never'}
                  </span>
                </div>
                <div className="breakdown-item">
                  <span className="breakdown-label">Updated By</span>
                  <span className="breakdown-value">{weights.updatedBy}</span>
                </div>
              </div>

              <form onSubmit={handleSubmit} className="admin-form">
                <div className="form-group">
                  <label htmlFor="netCarbonPosition">
                    Net Carbon Position Weight
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
                    Soil Organic Carbon Trend Weight
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
                    Management Practices Weight
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
                  <div style={{ 
                    padding: '10px', 
                    backgroundColor: isValidSum ? '#d4edda' : '#f8d7da',
                    borderRadius: '4px',
                    marginBottom: '10px'
                  }}>
                    <strong>Total:</strong> {(sum * 100).toFixed(1)}%
                    {!isValidSum && (
                      <span style={{ marginLeft: '10px', color: '#721c24' }}>
                        ⚠️ Must equal 100%
                      </span>
                    )}
                  </div>
                </div>

                <button 
                  type="submit" 
                  className="button"
                  disabled={submitting || !isValidSum}
                >
                  {submitting ? 'Updating...' : 'Update Weights'}
                </button>
              </form>

              <div style={{ marginTop: '30px', padding: '15px', backgroundColor: '#f8f9fa', borderRadius: '4px' }}>
                <h3 style={{ marginBottom: '10px' }}>About CRI Weights</h3>
                <p style={{ fontSize: '14px', color: '#666', lineHeight: '1.6' }}>
                  The Carbon Readiness Index (CRI) is calculated using a weighted combination of three components:
                </p>
                <ul style={{ marginTop: '10px', marginLeft: '20px', fontSize: '14px', color: '#666', lineHeight: '1.8' }}>
                  <li><strong>Net Carbon Position:</strong> Measures the farm's carbon balance (sequestration vs emissions)</li>
                  <li><strong>Soil Organic Carbon Trend:</strong> Tracks soil health improvement over time</li>
                  <li><strong>Management Practices:</strong> Evaluates sustainable farming practices</li>
                </ul>
                <p style={{ marginTop: '10px', fontSize: '14px', color: '#666', lineHeight: '1.6' }}>
                  Weights must sum to 1.0 (100%). Changes will affect all future CRI calculations.
                </p>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

export default AdminPanel;
