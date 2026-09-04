// src/data/mockData.ts
export interface RoomData {
  risks: number;
  score: number;
  critical: boolean;
}

export interface Detection {
  id: number;
  label?: string;
  type: string;          // e.g., 'obstacles', 'safety', etc.
  room: string;
  severity: 'high' | 'medium' | 'low';
  confidence: number;
  description?: string;
  recommendation?: string;
  x?: number;
  y?: number;
  width?: number;
  height?: number;
  coordinates?: { x: number; y: number }; // optional for 2D view
}

export interface RiskData {
  overallScore: number;
  totalRisks: number;
  highPriority: number;
  mediumPriority: number;
  lowPriority: number;
  rooms: Record<string, RoomData>;
  detections: Detection[];
}

// Minimal example
export const riskData: RiskData = {
  overallScore: 72,
  totalRisks: 16,
  highPriority: 6,
  mediumPriority: 7,
  lowPriority: 3,
  rooms: {
    bathroom: { risks: 5, score: 45, critical: true },
    bedroom: { risks: 4, score: 65, critical: false },
    living_room: { risks: 3, score: 78, critical: false },
  },
  detections: [],
};
