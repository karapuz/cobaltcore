import React, { useState } from 'react';
import { ArrowLeft, Activity, Loader, AlertCircle } from 'lucide-react';
import authService from '../services/authService';

// Field definitions with labels and default values
const FIELDS = [
  { key: 'computationId', label: 'Credit Rating Computation ID', type: 'text', hasBounds: false },
  { key: 'revenue', label: 'Revenue', type: 'number', hasBounds: true },
  { key: 'ebitdaMargin', label: 'EBITDA Margin %', type: 'number', hasBounds: true },
  { key: 'fcfToDebt', label: 'Free Cash Flow / Total Debt', type: 'number', hasBounds: true },
  { key: 'debtToEbitda', label: 'Total Debt / EBITDA', type: 'number', hasBounds: true },
  { key: 'netDebtToEbitda', label: 'Net Debt / EBITDA', type: 'number', hasBounds: true },
  { key: 'ebitdaToInterest', label: 'EBITDA / Interest', type: 'number', hasBounds: true },
  { key: 'roce', label: 'Return on Capital Employed %', type: 'number', hasBounds: true },
  { key: 'interestCoverage', label: 'Interest Coverage Ratio', type: 'number', hasBounds: true },
];

export default function ScenarioSurface({ user, onBack, initialData }) {
  // Form state
  const [formData, setFormData] = useState({
    computationId: 'CR-2024-001',
    revenue: 45200000,
    revenue_lower: 0,
    revenue_upper: 0,
    ebitdaMargin: 23.5,
    ebitdaMargin_lower: 0,
    ebitdaMargin_upper: 0,
    fcfToDebt: 0.15,
    fcfToDebt_lower: 0,
    fcfToDebt_upper: 0,
    debtToEbitda: 3.2,
    debtToEbitda_lower: 0,
    debtToEbitda_upper: 0,
    netDebtToEbitda: 2.8,
    netDebtToEbitda_lower: 0,
    netDebtToEbitda_upper: 0,
    ebitdaToInterest: 4.5,
    ebitdaToInterest_lower: 0,
    ebitdaToInterest_upper: 0,
    roce: 18.3,
    roce_lower: 0,
    roce_upper: 0,
    interestCoverage: 4.5,
    interestCoverage_lower: 0,
    interestCoverage_upper: 0,
  });

  // Populate form from initialData when passed from Scenarios
  React.useEffect(() => {
    if (initialData) {
      setFormData(prev => ({
        ...prev,
        computationId: initialData.id || prev.computationId,
        revenue: initialData.revenue || prev.revenue,
        ebitdaMargin: initialData.ebitdaMargin || prev.ebitdaMargin,
        fcfToDebt: initialData.fcfToDebt || prev.fcfToDebt,
        debtToEbitda: initialData.debtToEbitda || prev.debtToEbitda,
        netDebtToEbitda: initialData.netDebtToEbitda || prev.netDebtToEbitda,
        ebitdaToInterest: initialData.ebitdaToInterest || prev.ebitdaToInterest,
        roce: initialData.roce || prev.roce,
        interestCoverage: initialData.interestCoverage || prev.interestCoverage,
      }));
    }
  }, [initialData]);

  // Response state
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [responseId, setResponseId] = useState(null);
  const [isPolling, setIsPolling] = useState(false);
  const [plotData, setPlotData] = useState(null);
  const [error, setError] = useState(null);

  const handleChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const handleSubmit = async () => {
    setIsSubmitting(true);
    setError(null);
    setPlotData(null);

    // List of parameters that can have bounds
    const boundedParams = [
      'revenue', 'ebitdaMargin', 'fcfToDebt', 'debtToEbitda', 
      'netDebtToEbitda', 'ebitdaToInterest', 'roce', 'interestCoverage'
    ];

    // Count parameters with non-zero bounds
    const paramsWithBounds = boundedParams.filter(param => {
      const lowerBound = parseFloat(formData[`${param}_lower`]) || 0;
      const upperBound = parseFloat(formData[`${param}_upper`]) || 0;
      return lowerBound !== 0 || upperBound !== 0;
    });

    const boundsCount = paramsWithBounds.length;

    // Validate bounds count
    if (boundsCount === 0) {
      setError('Please specify non-zero bounds for at least one parameter (1D), two parameters (2D), or three parameters (3D).');
      setIsSubmitting(false);
      return;
    }

    if (boundsCount > 3) {
      setError(`Too many parameters with bounds. Please specify bounds for exactly 1 (1D), 2 (2D), or 3 (3D) parameters. Currently ${boundsCount} parameters have non-zero bounds.`);
      setIsSubmitting(false);
      return;
    }

    try {
      // Submit request
      const response = await authService.submitScenarioSurfaceRequest(formData);
      const { scenarioSurfaceResponseId } = response;
      
      setResponseId(scenarioSurfaceResponseId);
      setIsSubmitting(false);

      // Start polling
      if (response.status !== 'completed') {
        setIsPolling(true);
        pollForResponse(scenarioSurfaceResponseId);
      } else {
        // Already completed
        const result = await authService.getScenarioSurfaceResponse(scenarioSurfaceResponseId);
        setPlotData(result);
        setIsPolling(false);
      }
    } catch (err) {
      setError(err.message || 'Failed to submit request');
      setIsSubmitting(false);
    }
  };

  const pollForResponse = async (responseId) => {
    let attempts = 0;
    const maxAttempts = 60; // Poll for up to 60 seconds

    const poll = async () => {
      try {
        const result = await authService.getScenarioSurfaceResponse(responseId);
        
        if (result.status === 'completed') {
          setPlotData(result);
          setIsPolling(false);
          return;
        }

        // Continue polling
        attempts++;
        if (attempts < maxAttempts) {
          setTimeout(poll, 1000); // Poll every second
        } else {
          setError('Request timed out. Please try again.');
          setIsPolling(false);
        }
      } catch (err) {
        setError(err.message || 'Failed to fetch response');
        setIsPolling(false);
      }
    };

    poll();
  };

  return (
    <div className="min-h-screen bg-gray-50" style={{ paddingTop: '80px' }}>
      {/* Sub-header */}
      <div className="bg-white border-b border-gray-200 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-4">
              <button onClick={onBack} className="flex items-center text-gray-600 hover:text-gray-900 transition">
                <ArrowLeft className="w-5 h-5 mr-1" />
                <span className="text-sm font-medium">Back</span>
              </button>
              <div className="h-6 w-px bg-gray-300"></div>
              <div className="flex items-center gap-2">
                <Activity className="w-5 h-5 text-gray-700" />
                <h1 className="text-lg font-bold text-gray-900">Scenario Surface Analysis</h1>
              </div>
            </div>
            {user && (
              <div className="flex items-center gap-3">
                <span className="text-sm text-gray-500">
                  Welcome, <span className="font-semibold text-gray-800">{user.name}</span>
                </span>
              </div>
            )}
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Instructions */}
        <div className="bg-blue-50 border border-blue-200 rounded-xl p-5 mb-6">
          <div className="flex items-start gap-3">
            <Activity className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
            <div>
              <h3 className="text-sm font-semibold text-blue-900 mb-2">How to use Scenario Surface Analysis</h3>
              <ul className="text-sm text-blue-700 space-y-1">
                <li>• <strong>1D Analysis:</strong> Set non-zero bounds (% Lower and % Upper) for exactly <strong>one</strong> parameter</li>
                <li>• <strong>2D Analysis:</strong> Set non-zero bounds for exactly <strong>two</strong> parameters</li>
                <li>• <strong>3D Analysis:</strong> Set non-zero bounds for exactly <strong>three</strong> parameters</li>
                <li>• All other parameters will use their baseline values without variation</li>
              </ul>
            </div>
          </div>
        </div>

        {/* Upper Section - Parameters */}
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6 mb-8">
          <h2 className="text-xl font-bold text-gray-900 mb-6">Scenario Parameters</h2>
          
          <div className="space-y-6">
            {FIELDS.map(field => (
              <div key={field.key}>
                <label className="block text-sm font-semibold text-gray-700 mb-2">
                  {field.label}
                </label>
                
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  {/* Main value */}
                  <div>
                    <label className="block text-xs text-gray-500 mb-1">Value</label>
                    <input
                      type={field.type}
                      value={formData[field.key]}
                      onChange={(e) => handleChange(field.key, field.type === 'number' ? parseFloat(e.target.value) || 0 : e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      disabled={isSubmitting || isPolling}
                    />
                  </div>

                  {/* Lower bound */}
                  {field.hasBounds && (
                    <>
                      <div>
                        <label className="block text-xs text-gray-500 mb-1">% Lower Bound</label>
                        <input
                          type="number"
                          step="any"
                          value={formData[`${field.key}_lower`]}
                          onChange={(e) => {
                            const val = e.target.value;
                            // Allow empty string for clearing, otherwise parse as number
                            handleChange(`${field.key}_lower`, val === '' ? 0 : parseFloat(val));
                          }}
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                          disabled={isSubmitting || isPolling}
                        />
                      </div>

                      {/* Upper bound */}
                      <div>
                        <label className="block text-xs text-gray-500 mb-1">% Upper Bound</label>
                        <input
                          type="number"
                          step="any"
                          value={formData[`${field.key}_upper`]}
                          onChange={(e) => {
                            const val = e.target.value;
                            // Allow empty string for clearing, otherwise parse as number
                            handleChange(`${field.key}_upper`, val === '' ? 0 : parseFloat(val));
                          }}
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                          disabled={isSubmitting || isPolling}
                        />
                      </div>
                    </>
                  )}
                </div>
              </div>
            ))}
          </div>

          {/* Submit button */}
          <div className="mt-8 flex items-center gap-4">
            <button
              onClick={handleSubmit}
              disabled={isSubmitting || isPolling}
              className={`px-6 py-3 rounded-lg font-semibold text-white transition ${
                isSubmitting || isPolling
                  ? 'bg-gray-400 cursor-not-allowed'
                  : 'bg-blue-600 hover:bg-blue-700'
              }`}
            >
              {isSubmitting ? 'Submitting...' : isPolling ? 'Processing...' : 'Submit'}
            </button>

            {isPolling && (
              <div className="flex items-center gap-2 text-gray-600">
                <Loader className="w-5 h-5 animate-spin" />
                <span className="text-sm">Generating scenario surface...</span>
              </div>
            )}
          </div>

          {/* Error display */}
          {error && (
            <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg flex items-start gap-3">
              <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
              <div>
                <p className="text-sm font-semibold text-red-900">Error</p>
                <p className="text-sm text-red-700">{error}</p>
              </div>
            </div>
          )}
        </div>

        {/* Lower Section - Visualization */}
        {plotData && (
          <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6">
            <h2 className="text-xl font-bold text-gray-900 mb-6">
              Scenario Surface Results - {plotData.plot_type} Plot
            </h2>
            
            {plotData.plot_type === '1D' && <Plot1D data={plotData} formData={formData} />}
            {plotData.plot_type === '2D' && <Plot2D data={plotData} formData={formData} />}
            {plotData.plot_type === '3D' && <Plot3D data={plotData} formData={formData} />}
          </div>
        )}
      </div>
    </div>
  );
}

// 1D Line Plot Component
function Plot1D({ data, formData }) {
  const { param_name, timeseries } = data;
  const points = Object.values(timeseries);
  
  if (points.length === 0) return <p className="text-gray-500">No data available</p>;

  // Get mean value from formData (the baseline scenario)
  const meanVal = formData[param_name] || points.map(p => p[0]).reduce((sum, v) => sum + v, 0) / points.length;
  
  // Prevent division by zero
  if (meanVal === 0) {
    return <p className="text-red-500">Cannot normalize: baseline value is zero</p>;
  }
  
  // Normalize values as percentage deviation from mean
  const normalizedPoints = points.map(p => ({
    original: p[0],
    normalized: ((p[0] - meanVal) / meanVal) * 100,
    rating: p[1]
  }));
  
  // Filter out any invalid points
  const validPoints = normalizedPoints.filter(p => 
    !isNaN(p.normalized) && isFinite(p.normalized)
  );
  
  if (validPoints.length === 0) return <p className="text-red-500">No valid data points after normalization</p>;
  
  const normalizedValues = validPoints.map(p => p.normalized);
  const minNorm = Math.min(...normalizedValues);
  const maxNorm = Math.max(...normalizedValues);
  const range = maxNorm - minNorm || 1;

  return (
    <div>
      <p className="text-sm text-gray-600 mb-2">Parameter: <strong>{param_name}</strong></p>
      <p className="text-xs text-gray-500 mb-4">
        Y-axis shows % deviation from baseline ({meanVal.toLocaleString(undefined, { maximumFractionDigits: 2 })})
      </p>
      <div className="relative h-96 border border-gray-200 rounded-lg p-8">
        <svg width="100%" height="100%" viewBox="0 0 800 400" className="overflow-visible">
          {/* Axes */}
          <line x1="50" y1="350" x2="750" y2="350" stroke="#d1d5db" strokeWidth="2" />
          <line x1="50" y1="350" x2="50" y2="50" stroke="#d1d5db" strokeWidth="2" />
          
          {/* Zero line (baseline) */}
          <line 
            x1="50" 
            y1={350 - ((0 - minNorm) / range) * 300}
            x2="750" 
            y2={350 - ((0 - minNorm) / range) * 300}
            stroke="#9ca3af" 
            strokeWidth="1" 
            strokeDasharray="5,5" 
          />
          
          {/* Axis labels */}
          <text x="400" y="390" textAnchor="middle" className="text-xs fill-gray-600">
            {param_name}
          </text>
          <text x="20" y="200" textAnchor="middle" className="text-xs fill-gray-600" transform="rotate(-90 20 200)">
            % Deviation from Baseline
          </text>

          {/* Line and points */}
          <polyline
            points={validPoints.map((p, i) => {
              const x = 50 + (i / (validPoints.length - 1)) * 700;
              const y = 350 - ((p.normalized - minNorm) / range) * 300;
              return `${x},${y}`;
            }).join(' ')}
            fill="none"
            stroke="#3b82f6"
            strokeWidth="2"
          />

          {validPoints.map((point, i) => {
            const x = 50 + (i / (validPoints.length - 1)) * 700;
            const y = 350 - ((point.normalized - minNorm) / range) * 300;
            return (
              <g key={i}>
                <circle cx={x} cy={y} r="5" fill="#3b82f6" />
                <text x={x} y={y - 10} textAnchor="middle" className="text-xs font-bold fill-gray-900">
                  {point.rating}
                </text>
              </g>
            );
          })}
        </svg>
      </div>
    </div>
  );
}

// 2D Scatter Plot Component
function Plot2D({ data, formData }) {
  const { param_names, timeseries } = data;
  const points = Object.values(timeseries);
  
  if (points.length === 0) return <p className="text-gray-500">No data available</p>;

  // Get mean values from formData (the baseline scenario)
  const xValues = points.map(p => p[0]);
  const yValues = points.map(p => p[1]);
  const meanX = formData[param_names[0]] || xValues.reduce((sum, v) => sum + v, 0) / xValues.length;
  const meanY = formData[param_names[1]] || yValues.reduce((sum, v) => sum + v, 0) / yValues.length;
  
  // Prevent division by zero
  if (meanX === 0 || meanY === 0) {
    return <p className="text-red-500">Cannot normalize: baseline values contain zero</p>;
  }
  
  // Normalize as percentage deviation from mean
  const normalizedPoints = points.map(p => ({
    normX: ((p[0] - meanX) / meanX) * 100,
    normY: ((p[1] - meanY) / meanY) * 100,
    rating: p[2]
  }));
  
  // Filter out any invalid points
  const validPoints = normalizedPoints.filter(p => 
    !isNaN(p.normX) && !isNaN(p.normY) &&
    isFinite(p.normX) && isFinite(p.normY)
  );
  
  if (validPoints.length === 0) return <p className="text-red-500">No valid data points after normalization</p>;
  
  const normXValues = validPoints.map(p => p.normX);
  const normYValues = validPoints.map(p => p.normY);
  const minX = Math.min(...normXValues);
  const maxX = Math.max(...normXValues);
  const minY = Math.min(...normYValues);
  const maxY = Math.max(...normYValues);
  const rangeX = maxX - minX || 1;
  const rangeY = maxY - minY || 1;

  return (
    <div>
      <p className="text-sm text-gray-600 mb-2">
        Parameters: <strong>{param_names[0]}</strong> vs <strong>{param_names[1]}</strong>
      </p>
      <p className="text-xs text-gray-500 mb-4">
        Axes show % deviation from baseline ({meanX.toLocaleString(undefined, { maximumFractionDigits: 2 })}, {meanY.toLocaleString(undefined, { maximumFractionDigits: 2 })})
      </p>
      <div className="relative h-96 border border-gray-200 rounded-lg p-8">
        <svg width="100%" height="100%" viewBox="0 0 800 400" className="overflow-visible">
          {/* Axes */}
          <line x1="50" y1="350" x2="750" y2="350" stroke="#d1d5db" strokeWidth="2" />
          <line x1="50" y1="350" x2="50" y2="50" stroke="#d1d5db" strokeWidth="2" />
          
          {/* Zero lines (baseline) */}
          <line 
            x1={50 + ((0 - minX) / rangeX) * 700}
            y1="50" 
            x2={50 + ((0 - minX) / rangeX) * 700}
            y2="350"
            stroke="#9ca3af" 
            strokeWidth="1" 
            strokeDasharray="5,5" 
          />
          <line 
            x1="50"
            y1={350 - ((0 - minY) / rangeY) * 300}
            x2="750"
            y2={350 - ((0 - minY) / rangeY) * 300}
            stroke="#9ca3af" 
            strokeWidth="1" 
            strokeDasharray="5,5" 
          />
          
          {/* Axis labels */}
          <text x="400" y="390" textAnchor="middle" className="text-xs fill-gray-600">
            {param_names[0]} (% deviation)
          </text>
          <text x="20" y="200" textAnchor="middle" className="text-xs fill-gray-600" transform="rotate(-90 20 200)">
            {param_names[1]} (% deviation)
          </text>

          {/* Points */}
          {validPoints.map((point, i) => {
            const x = 50 + ((point.normX - minX) / rangeX) * 700;
            const y = 350 - ((point.normY - minY) / rangeY) * 300;
            return (
              <g key={i}>
                <circle cx={x} cy={y} r="6" fill="#8b5cf6" opacity="0.7" />
                <text x={x} y={y - 10} textAnchor="middle" className="text-xs font-bold fill-gray-900">
                  {point.rating}
                </text>
              </g>
            );
          })}
        </svg>
      </div>
    </div>
  );
}

// 3D Scatter Plot Component (simplified 2D projection)
function Plot3D({ data, formData }) {
  const { param_names, timeseries } = data;
  const points = Object.values(timeseries);
  
  if (points.length === 0) return <p className="text-gray-500">No data available</p>;

  // Get mean values from formData (the baseline scenario)
  const xValues = points.map(p => p[0]);
  const yValues = points.map(p => p[1]);
  const zValues = points.map(p => p[2]);
  const meanX = formData[param_names[0]] || xValues.reduce((sum, v) => sum + v, 0) / xValues.length;
  const meanY = formData[param_names[1]] || yValues.reduce((sum, v) => sum + v, 0) / yValues.length;
  const meanZ = formData[param_names[2]] || zValues.reduce((sum, v) => sum + v, 0) / zValues.length;
  
  // Prevent division by zero
  if (meanX === 0 || meanY === 0 || meanZ === 0) {
    return <p className="text-red-500">Cannot normalize: baseline values contain zero</p>;
  }
  
  // Normalize as percentage deviation from mean
  const normalizedPoints = points.map(p => ({
    normX: ((p[0] - meanX) / meanX) * 100,
    normY: ((p[1] - meanY) / meanY) * 100,
    normZ: ((p[2] - meanZ) / meanZ) * 100,
    rating: p[3]
  }));
  
  // Filter out any invalid points
  const validPoints = normalizedPoints.filter(p => 
    !isNaN(p.normX) && !isNaN(p.normY) && !isNaN(p.normZ) &&
    isFinite(p.normX) && isFinite(p.normY) && isFinite(p.normZ)
  );
  
  if (validPoints.length === 0) return <p className="text-red-500">No valid data points after normalization</p>;
  
  const normXValues = validPoints.map(p => p.normX);
  const normYValues = validPoints.map(p => p.normY);
  const normZValues = validPoints.map(p => p.normZ);
  const minX = Math.min(...normXValues);
  const maxX = Math.max(...normXValues);
  const minY = Math.min(...normYValues);
  const maxY = Math.max(...normYValues);
  const minZ = Math.min(...normZValues);
  const maxZ = Math.max(...normZValues);
  const rangeX = maxX - minX || 1;
  const rangeY = maxY - minY || 1;
  const rangeZ = maxZ - minZ || 1;

  return (
    <div>
      <p className="text-sm text-gray-600 mb-2">
        Parameters: <strong>{param_names[0]}</strong>, <strong>{param_names[1]}</strong>, <strong>{param_names[2]}</strong>
      </p>
      <p className="text-xs text-gray-500 mb-4">
        Axes show % deviation from baseline. Point size represents {param_names[2]} deviation.
      </p>
      <div className="relative h-96 border border-gray-200 rounded-lg p-8">
        <svg width="100%" height="100%" viewBox="0 0 800 400" className="overflow-visible">
          {/* Axes */}
          <line x1="50" y1="350" x2="750" y2="350" stroke="#d1d5db" strokeWidth="2" />
          <line x1="50" y1="350" x2="50" y2="50" stroke="#d1d5db" strokeWidth="2" />
          
          {/* Zero lines (baseline) */}
          <line 
            x1={50 + ((0 - minX) / rangeX) * 700}
            y1="50" 
            x2={50 + ((0 - minX) / rangeX) * 700}
            y2="350"
            stroke="#9ca3af" 
            strokeWidth="1" 
            strokeDasharray="5,5" 
          />
          <line 
            x1="50"
            y1={350 - ((0 - minY) / rangeY) * 300}
            x2="750"
            y2={350 - ((0 - minY) / rangeY) * 300}
            stroke="#9ca3af" 
            strokeWidth="1" 
            strokeDasharray="5,5" 
          />
          
          {/* Axis labels */}
          <text x="400" y="390" textAnchor="middle" className="text-xs fill-gray-600">
            {param_names[0]} (% deviation)
          </text>
          <text x="20" y="200" textAnchor="middle" className="text-xs fill-gray-600" transform="rotate(-90 20 200)">
            {param_names[1]} (% deviation)
          </text>

          {/* Points with size representing 3rd dimension */}
          {validPoints.map((point, i) => {
            const x = 50 + ((point.normX - minX) / rangeX) * 700;
            const y = 350 - ((point.normY - minY) / rangeY) * 300;
            const size = 4 + ((point.normZ - minZ) / rangeZ) * 12; // Size varies with 3rd dimension
            return (
              <g key={i}>
                <circle cx={x} cy={y} r={size} fill="#10b981" opacity="0.6" />
                <text x={x} y={y - size - 5} textAnchor="middle" className="text-xs font-bold fill-gray-900">
                  {point.rating}
                </text>
              </g>
            );
          })}
        </svg>
        
        <div className="mt-4 text-xs text-gray-500">
          Note: Point size represents {param_names[2]} % deviation (larger = higher positive deviation)
        </div>
      </div>
    </div>
  );
}