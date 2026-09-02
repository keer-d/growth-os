import { handleApi } from '@/hosting/api';

type RouteContext = { params: Promise<{ segments?: string[] }> };

async function route(request: Request, context: RouteContext) {
  const { segments = [] } = await context.params;
  return handleApi(request, segments);
}

export const GET = route;
export const POST = route;
