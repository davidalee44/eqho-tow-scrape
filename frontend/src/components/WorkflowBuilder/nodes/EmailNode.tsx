import React from 'react';
import { Handle, Position, NodeProps } from 'reactflow';

const EmailNode: React.FC<NodeProps> = ({ data, selected }) => {
  return (
    <div className={`email-node ${selected ? 'selected' : ''}`}>
      <div className="email-node-content">
        <div className="email-node-icon">📧</div>
        <div className="email-node-label">{data.label || 'Email'}</div>
        {data.subject && (
          <div className="email-node-subject">{data.subject}</div>
        )}
      </div>
      <Handle type="target" position={Position.Top} />
      <Handle type="source" position={Position.Bottom} />
    </div>
  );
};

export default EmailNode;

