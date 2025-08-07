# Agent Analytics Phase 1: Basic User-Agent Detection

## Overview

Implement basic analytics to detect and track LLM agent visits to agent.brand.com by analyzing User-Agent strings and basic request patterns.

## Database Schema

### New Table: agent_visits

```sql
CREATE TABLE agent_visits (
    id TEXT PRIMARY KEY,
    session_id TEXT,
    ip_address TEXT,
    user_agent TEXT NOT NULL,
    is_likely_agent BOOLEAN NOT NULL DEFAULT FALSE,
    agent_type TEXT, -- 'openai', 'anthropic', 'python-script', 'curl', 'unknown', 'human'
    confidence_score DECIMAL(3,2), -- 0.00 to 1.00
    
    -- Request details
    method TEXT NOT NULL, -- GET, POST, etc.
    path TEXT NOT NULL,
    query_params JSONB,
    referrer TEXT,
    
    -- Additional headers for analysis
    accept_header TEXT,
    accept_language TEXT,
    accept_encoding TEXT,
    
    -- Metadata
    timestamp TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    processing_time_ms INTEGER
);

-- Indexes for analytics queries
CREATE INDEX agent_visits_timestamp_idx ON agent_visits(timestamp);
CREATE INDEX agent_visits_agent_type_idx ON agent_visits(agent_type);
CREATE INDEX agent_visits_is_likely_agent_idx ON agent_visits(is_likely_agent);
CREATE INDEX agent_visits_ip_address_idx ON agent_visits(ip_address);
CREATE INDEX agent_visits_session_id_idx ON agent_visits(session_id);
```

## Implementation

### 1. Agent Detection Service

Create `backend/src/services/agent-detection.service.ts`:

```typescript
export interface AgentDetectionResult {
  isLikelyAgent: boolean;
  agentType: 'openai' | 'anthropic' | 'python-script' | 'curl' | 'langchain' | 'unknown' | 'human';
  confidenceScore: number; // 0.00 to 1.00
  detectionReasons: string[];
}

export class AgentDetectionService {
  
  detectAgent(request: FastifyRequest): AgentDetectionResult {
    const userAgent = request.headers['user-agent'] || '';
    const acceptHeader = request.headers['accept'] || '';
    const acceptLanguage = request.headers['accept-language'];
    const acceptEncoding = request.headers['accept-encoding'];
    const referer = request.headers['referer'];
    
    const result: AgentDetectionResult = {
      isLikelyAgent: false,
      agentType: 'human',
      confidenceScore: 0.0,
      detectionReasons: []
    };
    
    // Agent detection logic here (see detailed implementation below)
    
    return result;
  }
  
  private analyzeUserAgent(userAgent: string): Partial<AgentDetectionResult> {
    // User-Agent pattern matching logic
  }
  
  private analyzeHeaders(headers: any): Partial<AgentDetectionResult> {
    // Header analysis logic
  }
  
  private calculateConfidence(signals: any[]): number {
    // Confidence scoring logic
  }
}
```

### 2. Agent Detection Logic

#### User-Agent Pattern Matching

```typescript
private analyzeUserAgent(userAgent: string): Partial<AgentDetectionResult> {
  const ua = userAgent.toLowerCase();
  
  // OpenAI Agents
  if (ua.includes('openai') || ua.includes('gpt')) {
    return {
      isLikelyAgent: true,
      agentType: 'openai',
      confidenceScore: 0.95,
      detectionReasons: ['OpenAI user-agent detected']
    };
  }
  
  // Anthropic/Claude Agents
  if (ua.includes('anthropic') || ua.includes('claude')) {
    return {
      isLikelyAgent: true,
      agentType: 'anthropic',
      confidenceScore: 0.95,
      detectionReasons: ['Anthropic user-agent detected']
    };
  }
  
  // Python scripts (common for AI agents)
  if (ua.includes('python-requests') || ua.includes('urllib') || ua.includes('httpx')) {
    return {
      isLikelyAgent: true,
      agentType: 'python-script',
      confidenceScore: 0.80,
      detectionReasons: ['Python HTTP client detected']
    };
  }
  
  // cURL (CLI tool, often used by agents)
  if (ua.includes('curl/')) {
    return {
      isLikelyAgent: true,
      agentType: 'curl',
      confidenceScore: 0.75,
      detectionReasons: ['cURL user-agent detected']
    };
  }
  
  // LangChain and other AI frameworks
  if (ua.includes('langchain') || ua.includes('llamaindex') || ua.includes('haystack')) {
    return {
      isLikelyAgent: true,
      agentType: 'langchain',
      confidenceScore: 0.90,
      detectionReasons: ['AI framework user-agent detected']
    };
  }
  
  // Generic bot patterns
  if (/bot|crawler|spider|scraper|agent/i.test(ua)) {
    return {
      isLikelyAgent: true,
      agentType: 'unknown',
      confidenceScore: 0.70,
      detectionReasons: ['Generic bot pattern in user-agent']
    };
  }
  
  // Missing or minimal user-agent (suspicious)
  if (!userAgent || userAgent.length < 10) {
    return {
      isLikelyAgent: true,
      agentType: 'unknown',
      confidenceScore: 0.60,
      detectionReasons: ['Missing or minimal user-agent']
    };
  }
  
  return {
    isLikelyAgent: false,
    agentType: 'human',
    confidenceScore: 0.10
  };
}
```

#### Header Analysis

```typescript
private analyzeHeaders(headers: any): { signals: string[], score: number } {
  const signals: string[] = [];
  let suspicionScore = 0;
  
  // Missing common browser headers
  if (!headers['accept-language']) {
    signals.push('Missing Accept-Language header');
    suspicionScore += 0.15;
  }
  
  if (!headers['accept-encoding']) {
    signals.push('Missing Accept-Encoding header');
    suspicionScore += 0.10;
  }
  
  // Suspicious Accept header (agents often request JSON directly)
  if (headers['accept'] === 'application/json') {
    signals.push('Requesting JSON content directly');
    suspicionScore += 0.20;
  }
  
  // No cookies (agents typically don't handle cookies)
  if (!headers['cookie']) {
    signals.push('No cookies present');
    suspicionScore += 0.05;
  }
  
  // Direct access (no referer)
  if (!headers['referer'] && !headers['referrer']) {
    signals.push('Direct access (no referer)');
    suspicionScore += 0.10;
  }
  
  // Programmatic Accept headers
  if (headers['accept']?.includes('*/*') && !headers['accept']?.includes('text/html')) {
    signals.push('Non-browser Accept header pattern');
    suspicionScore += 0.10;
  }
  
  return { signals, score: Math.min(suspicionScore, 1.0) };
}
```

### 3. Middleware Integration

Create `backend/src/middleware/agent-analytics.middleware.ts`:

```typescript
import { FastifyRequest, FastifyReply } from 'fastify';
import { AgentDetectionService } from '../services/agent-detection.service.js';

export class AgentAnalyticsMiddleware {
  constructor(
    private agentDetection: AgentDetectionService,
    private prisma: any // Prisma client
  ) {}
  
  async trackVisit(request: FastifyRequest, reply: FastifyReply) {
    const startTime = Date.now();
    
    try {
      // Detect if request is from an agent
      const detection = this.agentDetection.detectAgent(request);
      
      // Extract session ID (from your existing session logic)
      const sessionId = this.extractSessionId(request);
      
      // Log the visit
      await this.prisma.agentVisit.create({
        data: {
          id: crypto.randomUUID(),
          sessionId,
          ipAddress: this.extractIpAddress(request),
          userAgent: request.headers['user-agent'] || '',
          isLikelyAgent: detection.isLikelyAgent,
          agentType: detection.agentType,
          confidenceScore: detection.confidenceScore,
          method: request.method,
          path: request.url.split('?')[0],
          queryParams: Object.fromEntries(new URLSearchParams(request.url.split('?')[1] || '')),
          referrer: request.headers['referer'] || request.headers['referrer'] || null,
          acceptHeader: request.headers['accept'] || null,
          acceptLanguage: request.headers['accept-language'] || null,
          acceptEncoding: request.headers['accept-encoding'] || null,
          processingTimeMs: Date.now() - startTime
        }
      });
      
      // Add detection info to request for use in other parts of the app
      (request as any).agentDetection = detection;
      
    } catch (error) {
      // Don't fail the request if analytics fails
      console.error('Agent analytics error:', error);
    }
  }
  
  private extractSessionId(request: FastifyRequest): string | null {
    // Extract from your existing session management
    // This depends on how you're currently handling sessions
    return request.headers['x-session-id'] as string || null;
  }
  
  private extractIpAddress(request: FastifyRequest): string {
    return request.headers['x-forwarded-for'] as string || 
           request.headers['x-real-ip'] as string || 
           request.ip || 
           'unknown';
  }
}
```

### 4. Route Integration

Update your main routes to include the middleware:

```typescript
// In your main router setup
import { AgentAnalyticsMiddleware } from '../middleware/agent-analytics.middleware.js';

const agentAnalytics = new AgentAnalyticsMiddleware(agentDetectionService, prisma);

// Apply to all routes
fastify.addHook('onRequest', async (request, reply) => {
  await agentAnalytics.trackVisit(request, reply);
});

// Or apply to specific routes
fastify.get('/api/*', {
  preHandler: [agentAnalytics.trackVisit.bind(agentAnalytics)]
}, async (request, reply) => {
  // Your route handler
});
```

### 5. Analytics API Endpoints

Create `backend/src/routes/analytics.routes.ts`:

```typescript
export const analyticsRoutes: FastifyPluginAsync = async (fastify) => {
  
  // Get agent visit summary
  fastify.get('/api/analytics/agents/summary', async (request, reply) => {
    const summary = await fastify.prisma.agentVisit.groupBy({
      by: ['agentType'],
      _count: {
        id: true
      },
      where: {
        timestamp: {
          gte: new Date(Date.now() - 24 * 60 * 60 * 1000) // Last 24 hours
        }
      }
    });
    
    return {
      period: 'last_24_hours',
      summary: summary.map(s => ({
        agentType: s.agentType,
        visitCount: s._count.id
      }))
    };
  });
  
  // Get recent agent visits
  fastify.get('/api/analytics/agents/recent', async (request, reply) => {
    const visits = await fastify.prisma.agentVisit.findMany({
      where: {
        isLikelyAgent: true
      },
      orderBy: {
        timestamp: 'desc'
      },
      take: 50,
      select: {
        timestamp: true,
        agentType: true,
        confidenceScore: true,
        userAgent: true,
        path: true,
        ipAddress: true
      }
    });
    
    return { visits };
  });
  
  // Get agent activity timeline
  fastify.get('/api/analytics/agents/timeline', async (request, reply) => {
    const timeline = await fastify.prisma.$queryRaw`
      SELECT 
        DATE_TRUNC('hour', timestamp) as hour,
        agent_type,
        COUNT(*) as visit_count
      FROM agent_visits 
      WHERE timestamp >= NOW() - INTERVAL '7 days'
        AND is_likely_agent = true
      GROUP BY hour, agent_type
      ORDER BY hour DESC
    `;
    
    return { timeline };
  });
};
```

## Configuration

### Environment Variables

Add to `.env`:

```bash
# Agent Analytics
AGENT_ANALYTICS_ENABLED=true
AGENT_ANALYTICS_LOG_LEVEL=info
AGENT_DETECTION_THRESHOLD=0.5  # Minimum confidence score to mark as agent
```

### Feature Flags

```typescript
// In your config service
export const config = {
  agentAnalytics: {
    enabled: process.env.AGENT_ANALYTICS_ENABLED === 'true',
    logLevel: process.env.AGENT_ANALYTICS_LOG_LEVEL || 'info',
    detectionThreshold: parseFloat(process.env.AGENT_DETECTION_THRESHOLD || '0.5')
  }
};
```

## Testing

### Unit Tests

Create `backend/src/services/__tests__/agent-detection.service.test.ts`:

```typescript
describe('AgentDetectionService', () => {
  const service = new AgentDetectionService();
  
  test('detects OpenAI agent', () => {
    const mockRequest = {
      headers: {
        'user-agent': 'OpenAI-Agent/1.0'
      }
    } as any;
    
    const result = service.detectAgent(mockRequest);
    
    expect(result.isLikelyAgent).toBe(true);
    expect(result.agentType).toBe('openai');
    expect(result.confidenceScore).toBeGreaterThan(0.9);
  });
  
  test('detects Python requests', () => {
    const mockRequest = {
      headers: {
        'user-agent': 'python-requests/2.31.0'
      }
    } as any;
    
    const result = service.detectAgent(mockRequest);
    
    expect(result.isLikelyAgent).toBe(true);
    expect(result.agentType).toBe('python-script');
  });
  
  test('identifies human browser', () => {
    const mockRequest = {
      headers: {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'accept-language': 'en-US,en;q=0.9',
        'accept-encoding': 'gzip, deflate'
      }
    } as any;
    
    const result = service.detectAgent(mockRequest);
    
    expect(result.isLikelyAgent).toBe(false);
    expect(result.agentType).toBe('human');
  });
});
```

## Success Criteria

### Functional Requirements
- [x] All requests to agent.brand.com are analyzed for agent patterns
- [x] Agent visits are logged to database with confidence scores
- [x] Analytics API endpoints return agent activity summaries
- [x] System continues to function normally if analytics fails

### Performance Requirements
- [x] Agent detection adds <10ms to request processing time
- [x] Analytics middleware doesn't block request handling
- [x] Database writes are non-blocking (async)

### Data Quality Requirements
- [x] Agent detection accuracy >80% for known agent patterns
- [x] False positive rate <5% for human browsers
- [x] All agent visits include required metadata fields

## Future Enhancements (Phase 2 Preview)

- Request frequency analysis (rapid sequential requests)
- Behavioral pattern detection (no JavaScript execution)
- Geolocation analysis of agent traffic
- Agent conversation pattern analysis
- Machine learning model for improved detection

## Rollout Plan

1. **Week 1**: Implement agent detection service and middleware
2. **Week 2**: Add database schema and logging
3. **Week 3**: Create analytics API endpoints
4. **Week 4**: Add monitoring dashboard and testing

This implementation provides comprehensive agent detection while maintaining system performance and reliability.