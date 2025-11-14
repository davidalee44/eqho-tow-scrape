import React from 'react';
import { Handle, Position, NodeProps } from 'reactflow';

const EndNode: React.FC<NodeProps> = ({ data }) => {
  return (
    <div className="end-node">
      <div className="end-node-content">
        <div className="end-node-icon">🏁</div>
        <div className="end-node-label">{data.label || 'End'}</div>
      </div>
      <Handle type="target" position={Position.Top} />
    </div>
  );
};

export default EndNode;

