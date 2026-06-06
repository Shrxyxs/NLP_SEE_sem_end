interface ScoreGaugeProps {
  score: number;       // 0-100
  size?: number;       // SVG size in px
  strokeWidth?: number;
  color?: string;
}

export default function ScoreGauge({
  score,
  size = 140,
  strokeWidth = 10,
  color = '#2D6A4F',
}: ScoreGaugeProps) {
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const progress = Math.max(0, Math.min(100, score));
  const offset = circumference - (progress / 100) * circumference;

  return (
    <div className="score-gauge">
      <div style={{ position: 'relative', width: size, height: size }}>
        <svg width={size} height={size} style={{ transform: 'rotate(-90deg)' }}>
          {/* Background circle */}
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="none"
            stroke="#E8E4DE"
            strokeWidth={strokeWidth}
          />
          {/* Progress circle */}
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="none"
            stroke={color}
            strokeWidth={strokeWidth}
            strokeDasharray={circumference}
            strokeDashoffset={offset}
            strokeLinecap="round"
            style={{ transition: 'stroke-dashoffset 0.8s ease' }}
          />
        </svg>
        <div
          style={{
            position: 'absolute',
            top: '50%',
            left: '50%',
            transform: 'translate(-50%, -50%)',
            textAlign: 'center',
          }}
        >
          <div style={{ fontSize: '2rem', fontWeight: 800, color: '#2C2C2C', lineHeight: 1 }}>
            {Math.round(score)}
          </div>
          <div style={{ fontSize: '0.8rem', color: '#6B7280' }}>/ 100</div>
        </div>
      </div>
    </div>
  );
}
