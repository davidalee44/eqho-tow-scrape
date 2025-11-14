import React from 'react';
import { Handle, Position, NodeProps } from 'reactflow';

const StartNode: React.FC<NodeProps> = ({ data }) => {
  return (
    <div className="start-node">
      <div className="start-node-content">
        <div className="start-node-icon">🚀</div>
        <div className="start-node-label">{data.label || 'Start'}</div>
      </div>
      <Handle type="source" position={Position.Bottom} />
    </div>
  );
};

export default StartNode;

