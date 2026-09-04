// YOLO Detection Data Interfaces
export interface YOLODetection {
  id: number;
  x: number;
  y: number;
  width: number;
  height: number;
  label: 'sofa' | 'couch' | 'bed' | 'grab_bar' | 'railing' | 'rug' | 'stairs' | 'step' | 'kerb';
  confidence: number;
  room?: string;
  frame_timestamp?: number;
}

export interface ProcessedRisk {
  id: number;
  type: 'fall_risk' | 'trip_hazard' | 'missing_safety' | 'mobility_risk';
  severity: 'high' | 'medium' | 'low';
  description: string;
  recommendation: string;
  affected_objects: YOLODetection[];
  risk_score: number;
  spatial_zone: { x: number; y: number; radius: number };
}

export interface RoomAnalysis {
  name: string;
  detections: YOLODetection[];
  safety_score: number;
  risk_count: number;
  critical_issues: ProcessedRisk[];
  coverage_percentage: number;
}

export interface DashboardData {
  total_detections: number;
  detection_confidence: number;
  rooms_analyzed: number;
  overall_safety_score: number;
  fall_risk_score: number;
  mobility_score: number;
  trip_hazard_index: number;
  safety_equipment_coverage: number;
  object_counts: Record<string, number>;
  detections: YOLODetection[];
  processed_risks: ProcessedRisk[];
  room_analyses: RoomAnalysis[];
}