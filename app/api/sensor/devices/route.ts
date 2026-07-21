// GET /api/sensor/devices
//
// Returns all registered devices from the standalone CarbonReady Supabase
// project, most recently seen first.
import { NextResponse } from 'next/server';
import { getDevices } from '@/lib/api/carbonready';
import { requireAuth } from '@/lib/api/auth';

export async function GET(request: Request) {
  const unauthorized = requireAuth(request);
  if (unauthorized) return unauthorized;

  const devices = await getDevices();
  return NextResponse.json(devices);
}
