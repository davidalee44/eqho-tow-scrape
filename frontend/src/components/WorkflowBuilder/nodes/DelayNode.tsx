import React from 'react';
import { Handle, Position, NodeProps } from 'reactflow';

const DelayNode: React.FC<NodeProps> = ({ data, selected }) => {
  const delayHours = data.delay_hours || 24;
  const delayText =
    delayHours < 24
      ? `${delayHours}h`
      : delayHours < 168
      ? `${Math.floor(delayHours / 24)}d`
      : `${Math.floor(delayHours / 168)}w`;

  return (
    <div className={`delay-node ${selected ? 'selected' : ''}`}>
      <div className="delay-node-content">
        <div className="delay-node-icon">⏱️</div>
        <div className="delay-node-label">{data.label || 'Delay'}</div>
        <div className="delay-node-time">{delayText}</div>
      </div>
      <Handle type="target" position={Position.Top} />
      <Handle type="source" position={Position.Bottom} />
    </div>
  );
};

export default DelayNode;

