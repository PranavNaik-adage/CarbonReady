# CarbonReady Web Dashboard

A minimal, functional web dashboard for the CarbonReady carbon intelligence platform. Built with React, TypeScript, and Vite.

## Features

### Dashboard View
- **Net Carbon Position Card**: Displays farm's carbon balance with classification (Net Carbon Sink/Source)
  - Annual sequestration and emissions breakdown
  - Carbon stock information
  - Staleness indicator for data > 24 hours old
  
- **Carbon Readiness Index Card**: Shows CRI score with detailed breakdown
  - Overall score and classification (Excellent/Moderate/Needs Improvement)
  - Component contributions (Net Carbon Position, SOC Trend, Management Practices)
  - Weighting transparency
  - SOC trend status with visual indicators
  
- **Latest Sensor Readings Card**: Displays real-time environmental data
  - Soil moisture, soil temperature, air temperature, humidity
  - Device information and validation status
  - Staleness indicator for readings > 24 hours old
  
- **Historical Trends Chart**: Visualizes 12-month carbon trends
  - Net carbon position over time
  - Sequestration vs emissions trends
  - CRI score progression

### Admin Panel
- View current CRI weighting configuration
- Update CRI weights with validation
  - Ensures weights sum to 100%
  - Real-time validation feedback
  - Version tracking
- Role-based access control (admin only)

## Technology Stack

- **React 18**: UI framework
- **TypeScript**: Type safety
- **Vite**: Build tool and dev server
- **Recharts**: Data visualization
- **React Router**: Client-side routing

## Getting Started

### Prerequisites

- Node.js 18+ and npm

### Installation

1. Navigate to the web-dashboard directory:
```bash
cd web-dashboard
```

2. Install dependencies:
```bash
npm install
```

3. Create environment configuration:
```bash
cp .env.example .env
```

4. Update `.env` with your API Gateway URL:
```
VITE_API_URL=https://your-api-gateway-url.execute-api.region.amazonaws.com/prod
```

### Development

Start the development server:
```bash
npm run dev
```

The dashboard will be available at `http://localhost:3000`

### Building for Production

Build the production bundle:
```bash
npm run build
```

The built files will be in the `dist/` directory.

Preview the production build:
```bash
npm run preview
```

## API Integration

The dashboard consumes the following Dashboard API endpoints:

- `GET /api/v1/farms/{farmId}/carbon-position` - Net carbon position data
- `GET /api/v1/farms/{farmId}/carbon-readiness-index` - CRI with breakdown
- `GET /api/v1/farms/{farmId}/sensor-data/latest` - Latest sensor readings
- `GET /api/v1/farms/{farmId}/historical-trends?days=365` - Historical trends
- `GET /api/v1/admin/cri-weights` - Current CRI weights (admin)
- `PUT /api/v1/admin/cri-weights` - Update CRI weights (admin only)

## Project Structure

```
web-dashboard/
├── src/
│   ├── components/          # Reusable UI components
│   │   ├── CarbonPositionCard.tsx
│   │   ├── CRICard.tsx
│   │   ├── SensorDataCard.tsx
│   │   └── HistoricalTrendsChart.tsx
│   ├── pages/              # Page components
│   │   ├── Dashboard.tsx
│   │   └── AdminPanel.tsx
│   ├── api.ts              # API client
│   ├── types.ts            # TypeScript type definitions
│   ├── App.tsx             # Main app component
│   ├── App.css             # Global styles
│   ├── main.tsx            # Entry point
│   └── index.css           # Base styles
├── index.html              # HTML template
├── package.json            # Dependencies
├── tsconfig.json           # TypeScript config
├── vite.config.ts          # Vite config
└── README.md               # This file
```

## Deployment

### Option 1: AWS S3 + CloudFront

1. Build the production bundle:
```bash
npm run build
```

2. Upload `dist/` contents to S3 bucket

3. Configure CloudFront distribution pointing to S3 bucket

4. Update API CORS settings to allow CloudFront domain

### Option 2: AWS Amplify

1. Connect GitHub repository to AWS Amplify

2. Configure build settings:
```yaml
version: 1
frontend:
  phases:
    preBuild:
      commands:
        - cd web-dashboard
        - npm ci
    build:
      commands:
        - npm run build
  artifacts:
    baseDirectory: web-dashboard/dist
    files:
      - '**/*'
  cache:
    paths:
      - node_modules/**/*
```

3. Set environment variables in Amplify console

## Authentication (Future Enhancement)

The dashboard is designed to integrate with Amazon Cognito for authentication:

1. Configure Cognito User Pool and App Client
2. Add authentication library (e.g., AWS Amplify Auth)
3. Implement login/logout flows
4. Add JWT token to API requests
5. Implement role-based access control

## Requirements Validation

This dashboard implementation satisfies the following requirements:

- **Requirement 10.1**: Displays current Net Carbon Position ✓
- **Requirement 10.2**: Displays Carbon Readiness Index with classification ✓
- **Requirement 10.3**: Displays SOC trend with visual indicators ✓
- **Requirement 10.4**: Displays sequestration vs emissions breakdown ✓
- **Requirement 10.5**: Displays historical trends (12 months) ✓
- **Requirement 10.6**: Displays latest sensor readings ✓
- **Requirement 10.7**: Shows staleness indicator for data > 24 hours ✓
- **Requirement 17.1**: Provides CRI component breakdown ✓
- **Requirement 17.2**: Shows weighting values used in calculation ✓

## License

Part of the CarbonReady platform.
