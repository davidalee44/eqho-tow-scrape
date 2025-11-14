import React from 'react';
import { Handle, Position, NodeProps } from 'reactflow';

const PhoneNode: React.FC<NodeProps> = ({ data, selected }) => {
  return (
    <div className={`phone-node ${selected ? 'selected' : ''}`}>
      <div className="phone-node-content">
        <div className="phone-node-icon">📞</div>
        <div className="phone-node-label">{data.label || 'Phone'}</div>
        {data.template && (
          <div className="phone-node-preview">
            {data.template.substring(0, 30)}...
          </div>
        )}
      </div>
      <Handle type="target" position={Position.Top} />
      <Handle type="source" position={Position.Bottom} />
    </div>
  );
};

export default PhoneNode;

