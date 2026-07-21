// GET /api/sensor/readings
//
// Returns sensor readings from the standalone CarbonReady Supabase project.
//
// Query params:
//   device_id  (required)  - which node to fetch
//   limit      (optional)  - max rows, default 50 (ignored when from/to given)
//   from, to   (optional)  - ISO timestamps; if BOTH present, returns the range
//
// When from and to are both provided, returns readings in that range;
// otherwise returns the latest `limit` readings.
import { NextResponse } from 'next/server';
import { getLatestReadings, getReadingsInRange } from '@/lib/api/carbonready';
import { requireAuth } from '@/lib/api/auth';

export async function GET(request: Request) {
  const unauthorized = requireAuth(request);
  if (unauthorized) return unauthorized;

  const { searchParams } = new URL(request.url);
  const deviceId = searchParams.get('device_id');
  const from = searchParams.get('from');
  const to = searchParams.get('to');
  const limitParam = searchParams.get('limit');

  if (!deviceId) {
    return NextResponse.json(
      { error: 'device_id query parameter is required' },
      { status: 400 }
    );
  }

  if (from && to) {
    const readings = await getReadingsInRange(deviceId, from, to);
    return NextResponse.json(readings);
  }

  const limit = limitParam ? parseInt(limitParam, 10) : 50;
  const safeLimit = Number.isFinite(limit) && limit > 0 ? limit : 50;

  const readings = await getLatestReadings(deviceId, safeLimit);
  return NextResponse.json(readings);
}
